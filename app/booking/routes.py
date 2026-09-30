"""Booking module routes."""

from datetime import datetime, timedelta, time as dtime

from flask import (
    Blueprint,
    redirect,
    request,
    jsonify,
    url_for,
    render_template,
    flash,
    session,
)
from app.models.booking import Booking
from app.models.customer import Customer
from app.models.barber import Barber
from app.models.service import Service
from app.models.package import Package
from app.models.coupon import Coupon
from app.extensions import db

booking_bp = Blueprint("booking", __name__)


# ============================================================
# Helper: get logged-in customer from session
# ============================================================
def _get_logged_customer():
    cid = session.get("customer_id")
    if not cid:
        return None
    return Customer.query.get(cid)


# ============================================================
# Booking form (GET)
# ============================================================
@booking_bp.route("/", methods=["GET"])
def booking_form():
    barbers = Barber.query.order_by(Barber.name).all()
    services = Service.query.order_by(Service.name).all()
    packages = Package.query.order_by(Package.name).all()

    return render_template(
        "booking.html",
        barbers=barbers,
        services=services,
        packages=packages,
        logged_customer=_get_logged_customer(),
    )


# ============================================================
# Available slots API
# ============================================================
@booking_bp.route("/available-slots")
def available_slots():
    barber_id = request.args.get("barber_id", type=int)
    date_str = request.args.get("date")
    duration = request.args.get("duration", 30, type=int)
    slot_step = 30

    if not barber_id or not date_str:
        return jsonify({"slots": [], "reason": "Missing barber or date."})

    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"slots": [], "reason": "Invalid date."})

    barber = Barber.query.get(barber_id)
    if not barber:
        return jsonify({"slots": [], "reason": "Barber not found."})

    # ---- Schedule lookup (fallback to default) ----
    weekday = d.weekday()
    open_time, close_time, is_closed = dtime(10, 0), dtime(22, 0), False
    offs = []

    try:
        from app.models.barber_schedule import BarberSchedule, BarberTimeOff

        sched = BarberSchedule.query.filter_by(
            barber_id=barber_id, day_of_week=weekday
        ).first()
        if sched:
            open_time = sched.open_time
            close_time = sched.close_time
            is_closed = sched.is_closed

        if is_closed:
            return jsonify({"slots": [], "reason": "Barber is off on this day."})

        offs = BarberTimeOff.query.filter_by(barber_id=barber_id, date=d).all()
        if any(o.all_day for o in offs):
            return jsonify({"slots": [], "reason": "Barber is on leave."})

    except Exception as e:
        # Fallback if schedule tables don't exist yet
        from flask import current_app

        current_app.logger.warning(f"Schedule lookup failed: {e}")

    # ---- Existing bookings ----
    bookings = Booking.query.filter(
        Booking.barber_id == barber_id,
        Booking.date == d,
        Booking.status != "Cancelled",
    ).all()

    start = datetime.combine(d, open_time)
    end = datetime.combine(d, close_time)
    now = datetime.now()

    slots = []
    current = start
    while current + timedelta(minutes=duration) <= end:
        slot_start = current
        slot_end = current + timedelta(minutes=duration)

        # Skip past times for today
        if d == now.date() and slot_start <= now:
            current += timedelta(minutes=slot_step)
            continue

        conflict = False

        for b in bookings:
            b_start = datetime.combine(b.date, b.time)
            b_end = b_start + timedelta(minutes=b.duration_minutes or 30)
            if slot_start < b_end and slot_end > b_start:
                conflict = True
                break

        if not conflict:
            for o in offs:
                if o.all_day:
                    conflict = True
                    break
                to_start = datetime.combine(d, o.start_time)
                to_end = datetime.combine(d, o.end_time)
                if slot_start < to_end and slot_end > to_start:
                    conflict = True
                    break

        if not conflict:
            slots.append(current.strftime("%H:%M"))

        current += timedelta(minutes=slot_step)

    return jsonify(
        {
            "slots": slots,
            "reason": None if slots else "No available slots on this day.",
        }
    )


# ============================================================
# Validate coupon API
# ============================================================
@booking_bp.route("/validate-coupon")
def validate_coupon():
    code = request.args.get("code", "").strip().upper()
    subtotal = request.args.get("subtotal", 0, type=float)

    if not code:
        return jsonify({"valid": False, "error": "No code provided."})

    coupon = Coupon.query.filter_by(code=code).first()
    if not coupon:
        return jsonify({"valid": False, "error": "Coupon not found."})

    ok, err = coupon.is_valid(subtotal)
    if not ok:
        return jsonify({"valid": False, "error": err})

    discount = coupon.compute_discount(subtotal)
    return jsonify(
        {
            "valid": True,
            "discount": round(discount, 2),
            "type": coupon.discount_type,
            "value": float(coupon.value),
        }
    )


# ============================================================
# Create booking (POST)
# ============================================================
@booking_bp.route("/create", methods=["POST"])
def create():
    # ==========================================================
    # 1) Collect form data
    # ==========================================================
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip().lower()
    barber_id = request.form.get("barber_id", type=int)
    date_str = request.form.get("date")
    time_str = request.form.get("time")
    booking_type = request.form.get("booking_type", "service")

    service_ids = request.form.getlist("service_ids", type=int)
    package_id = request.form.get("package_id", type=int)

    # ==========================================================
    # 2) Basic validation
    # ==========================================================
    if not all([name, phone, email, barber_id, date_str, time_str]):
        flash("All fields are required.", "error")
        return redirect(url_for("booking.booking_form"))

    barber = Barber.query.get(barber_id)
    if not barber:
        flash("Selected barber was not found. Please choose another.", "error")
        return redirect(url_for("booking.booking_form"))

    # ==========================================================
    # 3) Validate target (package OR services) + compute duration
    # ==========================================================
    package = None
    services = []

    if booking_type == "package":
        if not package_id:
            flash("Please select a package.", "error")
            return redirect(url_for("booking.booking_form"))

        package = Package.query.get(package_id)
        if not package:
            flash("Selected package was not found. Please choose another.", "error")
            return redirect(url_for("booking.booking_form"))

        duration_minutes = package.duration or 60

    elif booking_type == "service":
        if not service_ids:
            flash("Please select at least one service.", "error")
            return redirect(url_for("booking.booking_form"))

        services = Service.query.filter(Service.id.in_(service_ids)).all()
        if len(services) != len(service_ids):
            flash("One or more selected services no longer exist.", "error")
            return redirect(url_for("booking.booking_form"))

        duration_minutes = 30 * len(services)

    else:
        flash("Invalid booking type.", "error")
        return redirect(url_for("booking.booking_form"))

    # ==========================================================
    # 4) Parse date & time
    # ==========================================================
    try:
        booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        booking_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        flash("Invalid date or time format.", "error")
        return redirect(url_for("booking.booking_form"))

    # ==========================================================
    # 5) Find or create customer
    #    (logged-in customer takes priority)
    # ==========================================================
    logged_id = session.get("customer_id")

    if logged_id:
        customer = Customer.query.get(logged_id)
        if not customer:
            flash("Session expired. Please log in again.", "error")
            session.pop("customer_id", None)
            return redirect(url_for("customer.login"))

        customer.name = name or customer.name
        customer.phone = phone or customer.phone

    else:
        customer = Customer.query.filter_by(email=email).first()
        if not customer:
            customer = Customer(name=name, phone=phone or None, email=email)
            db.session.add(customer)
            db.session.flush()
        else:
            customer.name = name or customer.name
            customer.phone = phone or customer.phone

    # ==========================================================
    # 6) Coupon handling
    # ==========================================================
    coupon_code = request.form.get("coupon_code", "").strip().upper()
    coupon = None
    discount = 0

    subtotal = (
        float(package.price) if package else sum(float(s.price or 0) for s in services)
    )

    if coupon_code:
        coupon = Coupon.query.filter_by(code=coupon_code).first()
        if not coupon:
            flash(f"Coupon '{coupon_code}' not found.", "error")
        else:
            ok, err = coupon.is_valid(subtotal)
            if ok:
                discount = coupon.compute_discount(subtotal)
                coupon.used_count = (coupon.used_count or 0) + 1
                flash(f"Coupon applied — you saved ${discount:.2f}.", "success")
            else:
                flash(f"Coupon not applied: {err}", "error")
                coupon = None
                discount = 0

    # ==========================================================
    # 7) Create booking
    # ==========================================================
    booking = Booking(
        customer_id=customer.id,
        barber_id=barber.id,
        package_id=package.id if booking_type == "package" else None,
        coupon_id=coupon.id if coupon and discount > 0 else None,
        discount_amount=discount,
        duration_minutes=duration_minutes,
        date=booking_date,
        time=booking_time,
        status="Pending",
        payment_status="Unpaid",
    )

    if booking_type == "service":
        booking.services = services

    try:
        db.session.add(booking)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        from flask import current_app

        current_app.logger.exception(f"Booking commit failed: {e}")
        flash(
            "Something went wrong while saving your booking. Please try again.", "error"
        )
        return redirect(url_for("booking.booking_form"))

    flash("Your booking has been received! We'll confirm shortly.", "success")

    # Redirect logged-in customer to their dashboard
    if logged_id:
        return redirect(url_for("customer.dashboard"))
    return redirect(url_for("booking.booking_form"))


# ============================================================
# List bookings (JSON)
# ============================================================
@booking_bp.route("/list", methods=["GET"])
def list_bookings():
    try:
        page = int(request.args.get("page", 1))
    except (ValueError, TypeError):
        page = 1
    try:
        per_page = int(request.args.get("per_page", 10))
    except (ValueError, TypeError):
        per_page = 10

    pagination = Booking.query.paginate(page=page, per_page=per_page, error_out=False)
    bookings = [b.to_dict() for b in pagination.items]

    return jsonify(
        {
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "data": bookings,
        }
    )
