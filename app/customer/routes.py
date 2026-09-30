"""Customer account & self-service routes."""

from functools import wraps

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    session,
)
from app.models.customer import Customer
from app.models.booking import Booking
from app.extensions import db

customer_bp = Blueprint("customer", __name__, url_prefix="/account")


# ============================================================
# Decorator: require logged-in customer
# ============================================================
def customer_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("customer_id"):
            flash("Please log in to view this page.", "error")
            return redirect(url_for("customer.login", next=request.path))
        return func(*args, **kwargs)

    return wrapper


def current_customer():
    cid = session.get("customer_id")
    if not cid:
        return None
    return Customer.query.get(cid)


# ============================================================
# Register
# ============================================================
@customer_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("customer_id"):
        return redirect(url_for("customer.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        pw = request.form.get("password", "")
        pw2 = request.form.get("password_confirm", "")

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        if not pw or len(pw) < 6:
            errors.append("Password must be at least 6 characters.")
        if pw != pw2:
            errors.append("Passwords do not match.")

        existing = Customer.query.filter_by(email=email).first()
        if existing and existing.has_account:
            errors.append("An account with this email already exists.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "customer/register.html",
                name=name,
                email=email,
                phone=phone,
            )

        # Attach account to existing customer (created by admin/booking) OR create new
        if existing:
            customer = existing
            customer.name = customer.name or name
            customer.phone = customer.phone or phone
        else:
            customer = Customer(name=name, phone=phone or None, email=email)
            db.session.add(customer)

        customer.set_password(pw)
        db.session.commit()

        session["customer_id"] = customer.id
        flash(f"Welcome, {customer.name}!", "success")
        return redirect(url_for("customer.dashboard"))

    return render_template("customer/register.html")


# ============================================================
# Login
# ============================================================
@customer_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("customer_id"):
        return redirect(url_for("customer.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")

        customer = Customer.query.filter_by(email=email).first()
        if not customer or not customer.check_password(pw):
            flash("Invalid email or password.", "error")
            return render_template("customer/login.html", email=email)

        session["customer_id"] = customer.id
        flash(f"Welcome back, {customer.name}!", "success")

        next_url = request.args.get("next") or url_for("customer.dashboard")
        # Only allow same-site redirects
        if not next_url.startswith("/"):
            next_url = url_for("customer.dashboard")
        return redirect(next_url)

    return render_template("customer/login.html")


# ============================================================
# Logout
# ============================================================
@customer_bp.route("/logout", methods=["POST", "GET"])
def logout():
    session.pop("customer_id", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("home") if _has_home() else "/")


def _has_home():
    try:
        from flask import current_app

        return "home" in current_app.view_functions
    except Exception:
        return False


# ============================================================
# Dashboard — My Bookings
# ============================================================
@customer_bp.route("/")
@customer_required
def dashboard():
    customer = current_customer()

    bookings = (
        Booking.query.filter_by(customer_id=customer.id)
        .order_by(Booking.date.desc(), Booking.time.desc())
        .all()
    )

    total_spent = sum(b.compute_total() for b in bookings)
    upcoming = [b for b in bookings if b.status in ("Pending", "Confirmed")]

    return render_template(
        "customer/dashboard.html",
        customer=customer,
        bookings=bookings,
        upcoming=upcoming,
        total_spent=total_spent,
    )


# ============================================================
# Booking detail (customer view)
# ============================================================
@customer_bp.route("/bookings/<int:booking_id>")
@customer_required
def booking_detail(booking_id):
    customer = current_customer()
    booking = Booking.query.filter_by(
        id=booking_id, customer_id=customer.id
    ).first_or_404()

    return render_template(
        "customer/booking_detail.html", booking=booking, customer=customer
    )


# ============================================================
# Profile edit (optional)
# ============================================================
@customer_bp.route("/profile", methods=["GET", "POST"])
@customer_required
def profile():
    customer = current_customer()

    if request.method == "POST":
        customer.name = request.form.get("name", "").strip() or customer.name
        customer.phone = request.form.get("phone", "").strip() or None

        new_pw = request.form.get("password", "").strip()
        new_pw2 = request.form.get("password_confirm", "").strip()
        if new_pw:
            if len(new_pw) < 6:
                flash("Password must be at least 6 characters.", "error")
                return redirect(url_for("customer.profile"))
            if new_pw != new_pw2:
                flash("Passwords do not match.", "error")
                return redirect(url_for("customer.profile"))
            customer.set_password(new_pw)

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("customer.profile"))

    return render_template("customer/profile.html", customer=customer)
