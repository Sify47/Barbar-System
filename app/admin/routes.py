"""Admin route definitions"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from functools import wraps

from app.extensions import db
from app.models.admin import Admin
from app.models.barber import Barber
from app.models.service import Service
from app.models.booking import Booking
from app.models.customer import Customer

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
@admin_bp.route("/")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html")

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
        phone = request.form.get("phone")
        if not name:
            flash("Name is required")
            return redirect(url_for("admin.add_barber"))
        barber = Barber(name=name, phone=phone)
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
        barber.phone = request.form.get("phone")
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
# Services CRUD
# ------------------------------------------------------------------
@admin_bp.route("/services")
@admin_required
def list_services():
    page = request.args.get("page", 1, type=int)
    pagination = Service.query.paginate(page=page, per_page=10, error_out=False)
    return render_template("admin/services.html", pagination=pagination)

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

# ------------------------------------------------------------------
# Bookings view
# ------------------------------------------------------------------
@admin_bp.route("/bookings")
@admin_required
def list_bookings():
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status")
    barber_id = request.args.get("barber_id", type=int)
    query = Booking.query
    if status:
        query = query.filter_by(status=status)
    if barber_id:
        query = query.filter_by(barber_id=barber_id)
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    return render_template("admin/bookings.html", pagination=pagination, status=status, barber_id=barber_id)


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
