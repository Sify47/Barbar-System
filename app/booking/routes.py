"""Booking module routes."""

from datetime import datetime, date, time

from flask import Blueprint, redirect, request, jsonify, url_for, render_template, flash
from app.models.booking import Booking
from app.models.customer import Customer
from app.models.barber import Barber
from app.models.service import Service
from app.extensions import db

booking_bp = Blueprint("booking", __name__)


@booking_bp.route("/", methods=["GET"])
def booking_form():
    """Display the booking form."""
    barbers = Barber.query.all()
    services = Service.query.all()
    return render_template("booking.html", barbers=barbers, services=services)


@booking_bp.route("/create", methods=["POST"])
def create():
    """Handle booking submission."""
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    barber_id = request.form.get("barber_id", type=int)
    service_id = request.form.get("service_id", type=int)
    date_str = request.form.get("date")
    time_str = request.form.get("time")

    # Basic validation
    if not all([name, phone, email, barber_id, service_id, date_str, time_str]):
        flash("All fields are required.", "error")
        return redirect(url_for("booking.booking_form"))

    try:
        booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        booking_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        flash("Invalid date or time format.", "error")
        return redirect(url_for("booking.booking_form"))

    # Find or create customer
    customer = Customer.query.filter_by(email=email).first()
    if not customer:
        customer = Customer(name=name, phone=phone, email=email)
        db.session.add(customer)
        db.session.commit()

    # Create booking
    booking = Booking(
        customer_id=customer.id,
        barber_id=barber_id,
        service_id=service_id,
        date=booking_date,
        time=booking_time,
        status="Pending",
        payment_status="Unpaid",
    )
    db.session.add(booking)
    db.session.commit()

    flash("Your booking has been received! We'll confirm shortly.", "success")
    return redirect(url_for("booking.booking_form"))


@booking_bp.route("/list", methods=["GET"])
def list_bookings():
    """Paginated JSON list of bookings."""
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
    response = {
        "page": page,
        "per_page": per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "data": bookings,
    }
    return jsonify(response)
