"""Admin route definitions"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from functools import wraps
from app.models.coupon import Coupon

from app.extensions import db
from app.models.admin import Admin
from app.models.barber import Barber
from app.models.service import Service
from app.models.booking import Booking
from app.models.customer import Customer
from app.models.package import Package
from app.models.barber_schedule import BarberSchedule, BarberTimeOff
from datetime import datetime, time as dtime

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# Helper to enforce admin role
def admin_required(func):
    @login_required
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not isinstance(current_user, Admin):
            flash("Admin access required")
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)

    return wrapper


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------
from datetime import date, datetime, timedelta
from sqlalchemy import func


@admin_bp.route("/")
@admin_required
def dashboard():
    today = date.today()
    start_of_month = today.replace(day=1)
    week_ago = today - timedelta(days=7)

    # ---------- KPI counts ----------
    total_bookings = Booking.query.count()
    today_bookings = Booking.query.filter(Booking.date == today).count()
    week_bookings = Booking.query.filter(Booking.date >= week_ago).count()
    month_bookings = Booking.query.filter(Booking.date >= start_of_month).count()

    total_customers = Customer.query.count()
    new_customers_week = (
        Customer.query.filter(
            Customer.created_at >= datetime.combine(week_ago, datetime.min.time())
        ).count()
        if hasattr(Customer, "created_at")
        else 0
    )

    pending_count = Booking.query.filter(Booking.status == "Pending").count()
    confirmed_count = Booking.query.filter(Booking.status == "Confirmed").count()
    completed_count = Booking.query.filter(Booking.status == "Completed").count()
    cancelled_count = Booking.query.filter(Booking.status == "Cancelled").count()

    # ---------- Revenue (this month) ----------
    month_paid = (
        Booking.query.filter(Booking.date >= start_of_month)
        .filter(Booking.status != "Cancelled")
        .all()
    )
    month_revenue = sum(b.compute_total() for b in month_paid)

    today_paid = Booking.query.filter(Booking.date == today).all()
    today_revenue = sum(b.compute_total() for b in today_paid)

    # ---------- Recent bookings ----------
    recent_bookings = Booking.query.order_by(Booking.id.desc()).limit(8).all()

    # ---------- Today's schedule ----------
    todays_schedule = (
        Booking.query.filter(Booking.date == today)
        .filter(Booking.status != "Cancelled")
        .order_by(Booking.time)
        .all()
    )

    # ---------- Top barbers ----------
    top_barbers = (
        db.session.query(
            Barber.id,
            Barber.name,
            func.count(Booking.id).label("booking_count"),
        )
        .join(Booking, Booking.barber_id == Barber.id)
        .filter(Booking.status != "Cancelled")
        .group_by(Barber.id, Barber.name)
        .order_by(func.count(Booking.id).desc())
        .limit(5)
        .all()
    )

    # ---------- Popular services ----------
    from app.models.booking import booking_services

    popular_services = (
        db.session.query(
            Service.id,
            Service.name,
            func.count(booking_services.c.booking_id).label("use_count"),
        )
        .join(booking_services, booking_services.c.service_id == Service.id)
        .group_by(Service.id, Service.name)
        .order_by(func.count(booking_services.c.booking_id).desc())
        .limit(5)
        .all()
    )

    # ---------- 14-day trend ----------
    revenue_labels = []
    revenue_data = []
    bookings_data = []

    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        revenue_labels.append(d.strftime("%b %d"))

        day_bookings = (
            Booking.query.filter(Booking.date == d)
            .filter(Booking.status != "Cancelled")
            .all()
        )
        bookings_data.append(len(day_bookings))
        revenue_data.append(sum(b.compute_total() for b in day_bookings))

    return render_template(
        "admin/dashboard.html",
        # KPIs
        total_bookings=total_bookings,
        today_bookings=today_bookings,
        week_bookings=week_bookings,
        month_bookings=month_bookings,
        total_customers=total_customers,
        new_customers_week=new_customers_week,
        month_revenue=month_revenue,
        today_revenue=today_revenue,
        # Status
        pending_count=pending_count,
        confirmed_count=confirmed_count,
        completed_count=completed_count,
        cancelled_count=cancelled_count,
        # Lists
        recent_bookings=recent_bookings,
        todays_schedule=todays_schedule,
        top_barbers=top_barbers,
        popular_services=popular_services,
        # Chart data
        revenue_labels=revenue_labels,
        revenue_data=revenue_data,
        bookings_data=bookings_data,
    )


# ------------------------------------------------------------------
# Barbers CRUD
# ------------------------------------------------------------------
@admin_bp.route("/barbers")
@admin_required
def list_barbers():
    page = request.args.get("page", 1, type=int)
    pagination = Barber.query.paginate(page=page, per_page=10, error_out=False)
    return render_template("admin/barbers.html", pagination=pagination)


@admin_bp.route("/barbers/add", methods=["GET", "POST"])
@admin_required
def add_barber():
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            flash("Name is required")
            return redirect(url_for("admin.add_barber"))
        barber = Barber(name=name)
        db.session.add(barber)
        db.session.commit()
        return redirect(url_for("admin.list_barbers"))
    return render_template("admin/barber_form.html")


@admin_bp.route("/barbers/<int:barber_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_barber(barber_id):
    barber = Barber.query.get_or_404(barber_id)
    if request.method == "POST":
        barber.name = request.form.get("name")
        db.session.commit()
        return redirect(url_for("admin.list_barbers"))
    return render_template("admin/barber_form.html", barber=barber)


@admin_bp.route("/barbers/<int:barber_id>/delete", methods=["POST"])
@admin_required
def delete_barber(barber_id):
    barber = Barber.query.get_or_404(barber_id)
    db.session.delete(barber)
    db.session.commit()
    return redirect(url_for("admin.list_barbers"))


# ------------------------------------------------------------------
# Booking details
# ------------------------------------------------------------------
@admin_bp.route("/bookings/<int:booking_id>")
@admin_required
def booking_detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template("admin/booking_detail.html", booking=booking)


# ------------------------------------------------------------------
# Customer details (with their bookings)
# ------------------------------------------------------------------
@admin_bp.route("/customers/<int:customer_id>")
@admin_required
def customer_detail(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    # جيب كل حجوزات العميل مرتبة بالأحدث
    bookings = (
        Booking.query.filter_by(customer_id=customer.id)
        .order_by(Booking.date.desc(), Booking.time.desc())
        .all()
    )

    # احسب الإجمالي الكلي لكل حجوزات العميل
    total_spent = sum(b.compute_total() for b in bookings)

    return render_template(
        "admin/customer_detail.html",
        customer=customer,
        bookings=bookings,
        total_spent=total_spent,
    )


# ------------------------------------------------------------------
# Services + Packages (same page, tabbed)
# ------------------------------------------------------------------
@admin_bp.route("/services")
@admin_required
def list_services():
    """Show services & packages in one page with two tabs."""
    services_page = request.args.get("services_page", 1, type=int)
    packages_page = request.args.get("packages_page", 1, type=int)

    services_pagination = Service.query.order_by(Service.id.desc()).paginate(
        page=services_page, per_page=10, error_out=False
    )
    packages_pagination = Package.query.order_by(Package.id.desc()).paginate(
        page=packages_page, per_page=6, error_out=False
    )

    return render_template(
        "admin/services.html",
        services_pagination=services_pagination,
        packages_pagination=packages_pagination,
    )


@admin_bp.route("/bookings/<int:booking_id>/status", methods=["POST"])
@admin_required
def update_booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    new_status = request.form.get("status")
    if new_status in ("Pending", "Confirmed", "Completed", "Cancelled"):
        booking.status = new_status

    new_payment = request.form.get("payment_status")
    if new_payment in ("Unpaid", "Paid", "Refunded"):
        booking.payment_status = new_payment

    db.session.commit()
    flash("Booking updated.", "success")
    return redirect(url_for("admin.booking_detail", booking_id=booking.id))


@admin_bp.route("/coupons")
@admin_required
def list_coupons():
    page = request.args.get("page", 1, type=int)
    pagination = Coupon.query.order_by(Coupon.id.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template("admin/coupons.html", pagination=pagination)


@admin_bp.route("/coupons/add", methods=["GET", "POST"])
@admin_required
def add_coupon():
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        if not code:
            flash("Code is required.", "error")
            return redirect(url_for("admin.add_coupon"))
        if Coupon.query.filter_by(code=code).first():
            flash("This code already exists.", "error")
            return redirect(url_for("admin.add_coupon"))

        c = Coupon(
            code=code,
            description=request.form.get("description", "").strip() or None,
            discount_type=request.form.get("discount_type", "percent"),
            value=request.form.get("value", type=float) or 0,
            min_amount=request.form.get("min_amount", type=float) or 0,
            max_uses=request.form.get("max_uses", type=int),
            valid_from=_parse_date(request.form.get("valid_from")),
            valid_to=_parse_date(request.form.get("valid_to")),
            is_active=request.form.get("is_active") == "on",
        )
        db.session.add(c)
        db.session.commit()
        flash("Coupon created.", "success")
        return redirect(url_for("admin.list_coupons"))
    return render_template("admin/coupon_form.html", coupon=None)


@admin_bp.route("/coupons/<int:coupon_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_coupon(coupon_id):
    c = Coupon.query.get_or_404(coupon_id)
    if request.method == "POST":
        c.code = request.form.get("code", "").strip().upper()
        c.description = request.form.get("description", "").strip() or None
        c.discount_type = request.form.get("discount_type", "percent")
        c.value = request.form.get("value", type=float) or 0
        c.min_amount = request.form.get("min_amount", type=float) or 0
        c.max_uses = request.form.get("max_uses", type=int)
        c.valid_from = _parse_date(request.form.get("valid_from"))
        c.valid_to = _parse_date(request.form.get("valid_to"))
        c.is_active = request.form.get("is_active") == "on"
        db.session.commit()
        flash("Coupon updated.", "success")
        return redirect(url_for("admin.list_coupons"))
    return render_template("admin/coupon_form.html", coupon=c)


@admin_bp.route("/coupons/<int:coupon_id>/delete", methods=["POST"])
@admin_required
def delete_coupon(coupon_id):
    c = Coupon.query.get_or_404(coupon_id)
    db.session.delete(c)
    db.session.commit()
    flash("Coupon deleted.", "success")
    return redirect(url_for("admin.list_coupons"))


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


@admin_bp.route("/barbers/<int:barber_id>/schedule", methods=["GET", "POST"])
@admin_required
def barber_schedule(barber_id):
    barber = Barber.query.get_or_404(barber_id)

    if request.method == "POST":
        for day in range(7):
            is_closed = request.form.get(f"closed_{day}") == "on"
            open_str = request.form.get(f"open_{day}")
            close_str = request.form.get(f"close_{day}")

            sched = barber.schedule_for(day)
            if not sched:
                sched = BarberSchedule(
                    barber_id=barber.id,
                    day_of_week=day,
                    open_time=dtime(10, 0),
                    close_time=dtime(22, 0),
                )
                db.session.add(sched)

            if is_closed:
                sched.is_closed = True
            else:
                sched.is_closed = False
                try:
                    sched.open_time = datetime.strptime(open_str, "%H:%M").time()
                    sched.close_time = datetime.strptime(close_str, "%H:%M").time()
                except (ValueError, TypeError):
                    pass

        db.session.commit()
        flash("Schedule updated.", "success")
        return redirect(url_for("admin.barber_schedule", barber_id=barber.id))

    # Ensure each weekday has a row (defaults)
    for day in range(7):
        if not barber.schedule_for(day):
            s = BarberSchedule(
                barber_id=barber.id,
                day_of_week=day,
                open_time=dtime(10, 0),
                close_time=dtime(22, 0),
            )
            db.session.add(s)
    db.session.commit()

    return render_template(
        "admin/barber_schedule.html",
        barber=barber,
        weekdays=WEEKDAYS,
    )


@admin_bp.route("/barbers/<int:barber_id>/time-off/add", methods=["POST"])
@admin_required
def add_time_off(barber_id):
    barber = Barber.query.get_or_404(barber_id)
    date_str = request.form.get("date")
    all_day = request.form.get("all_day") == "on"
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        flash("Invalid date.", "error")
        return redirect(url_for("admin.barber_schedule", barber_id=barber.id))

    off = BarberTimeOff(
        barber_id=barber.id,
        date=d,
        all_day=all_day,
        start_time=(
            None
            if all_day
            else datetime.strptime(
                request.form.get("start_time", "10:00"), "%H:%M"
            ).time()
        ),
        end_time=(
            None
            if all_day
            else datetime.strptime(
                request.form.get("end_time", "14:00"), "%H:%M"
            ).time()
        ),
        reason=request.form.get("reason", "").strip() or None,
    )
    db.session.add(off)
    db.session.commit()
    flash("Time off added.", "success")
    return redirect(url_for("admin.barber_schedule", barber_id=barber.id))


@admin_bp.route("/time-off/<int:off_id>/delete", methods=["POST"])
@admin_required
def delete_time_off(off_id):
    off = BarberTimeOff.query.get_or_404(off_id)
    barber_id = off.barber_id
    db.session.delete(off)
    db.session.commit()
    return redirect(url_for("admin.barber_schedule", barber_id=barber_id))


# ---------- Services CRUD ----------
@admin_bp.route("/services/add", methods=["GET", "POST"])
@admin_required
def add_service():
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price", type=float)
        if not name or price is None:
            flash("Name and price required")
            return redirect(url_for("admin.add_service"))
        service = Service(name=name, price=price)
        db.session.add(service)
        db.session.commit()
        return redirect(url_for("admin.list_services"))
    return render_template("admin/service_form.html")


@admin_bp.route("/services/<int:service_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    if request.method == "POST":
        service.name = request.form.get("name")
        service.price = request.form.get("price", type=float)
        db.session.commit()
        return redirect(url_for("admin.list_services"))
    return render_template("admin/service_form.html", service=service)


@admin_bp.route("/services/<int:service_id>/delete", methods=["POST"])
@admin_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    return redirect(url_for("admin.list_services"))


# ---------- Packages CRUD ----------
@admin_bp.route("/packages/add", methods=["GET", "POST"])
@admin_required
def add_package():
    services = Service.query.order_by(Service.name).all()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", type=float)
        duration = request.form.get("duration", type=int)
        service_ids = request.form.getlist("service_ids", type=int)

        if not name or price is None:
            flash("Name and price are required.")
            return redirect(url_for("admin.add_package"))

        pkg = Package(
            name=name,
            description=description or None,
            price=price,
            duration=duration,
        )
        if service_ids:
            pkg.services = Service.query.filter(Service.id.in_(service_ids)).all()

        db.session.add(pkg)
        db.session.commit()
        flash("Package created.")
        return redirect(url_for("admin.list_services") + "#packages")

    return render_template("admin/package_form.html", package=None, services=services)


@admin_bp.route("/packages/<int:package_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_package(package_id):
    package = Package.query.get_or_404(package_id)
    services = Service.query.order_by(Service.name).all()

    if request.method == "POST":
        package.name = request.form.get("name", "").strip()
        package.description = request.form.get("description", "").strip() or None
        package.price = request.form.get("price", type=float)
        package.duration = request.form.get("duration", type=int)
        service_ids = request.form.getlist("service_ids", type=int)

        package.services = (
            Service.query.filter(Service.id.in_(service_ids)).all()
            if service_ids
            else []
        )

        db.session.commit()
        flash("Package updated.")
        return redirect(url_for("admin.list_services") + "#packages")

    return render_template(
        "admin/package_form.html", package=package, services=services
    )


@admin_bp.route("/packages/<int:package_id>/delete", methods=["POST"])
@admin_required
def delete_package(package_id):
    package = Package.query.get_or_404(package_id)
    db.session.delete(package)
    db.session.commit()
    flash("Package deleted.")
    return redirect(url_for("admin.list_services") + "#packages")


# ------------------------------------------------------------------
# Bookings view
# ------------------------------------------------------------------
@admin_bp.route("/bookings")
@admin_required
def list_bookings():
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "").strip()
    barber_id = request.args.get("barber_id", type=int)

    query = Booking.query

    if status:
        query = query.filter(Booking.status.ilike(status))
    if barber_id:
        query = query.filter(Booking.barber_id == barber_id)

    pagination = query.order_by(Booking.id.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    barbers = Barber.query.order_by(Barber.name).all()

    return render_template(
        "admin/bookings.html",
        pagination=pagination,
        status=status,
        barber_id=barber_id,
        barbers=barbers,
    )


# ------------------------------------------------------------------
# Customers CRUD
# ------------------------------------------------------------------
@admin_bp.route("/customers")
@admin_required
def list_customers():
    page = request.args.get("page", 1, type=int)
    pagination = db.session.query(Customer).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template("admin/customers.html", pagination=pagination)


@admin_bp.route("/customers/add", methods=["GET", "POST"])
@admin_required
def add_customer():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        if not name:
            flash("Name required")
            return redirect(url_for("admin.add_customer"))
        customer = Customer(name=name, phone=phone)
        db.session.add(customer)
        db.session.commit()
        return redirect(url_for("admin.list_customers"))
    return render_template("admin/customer_form.html")


@admin_bp.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == "POST":
        customer.name = request.form.get("name")
        customer.phone = request.form.get("phone")
        db.session.commit()
        return redirect(url_for("admin.list_customers"))
    return render_template("admin/customer_form.html", customer=customer)


@admin_bp.route("/customers/<int:customer_id>/delete", methods=["POST"])
@admin_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    return redirect(url_for("admin.list_customers"))
