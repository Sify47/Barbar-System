"""Booking module routes (placeholder)."""

from datetime import datetime

from flask import Blueprint, redirect, request, jsonify, url_for
from app.models.booking import Booking
from app.extensions import db
from app.models.customer import Customer

booking_bp = Blueprint("booking", __name__)


# app/booking/routes.py
@booking_bp.route("/create", methods=["POST"])
def create():
    # gather form data
    name = request.form.get("name")
    phone = request.form.get("phone")
    email = request.form.get("email")
    barber_id = request.form.get("barber_id", type=int)
    service_id = request.form.get("service_id", type=int)
    date = request.form.get("date")  # YYYY-MM-DD
    time = request.form.get("time")  # HH:MM

    # find or create customer
    customer = Customer.query.filter_by(email=email).first()
    if not customer:
        customer = Customer(name=name, phone=phone, email=email)
        db.session.add(customer)
        db.session.commit()

    # create booking
    booking = Booking(
        customer_id=customer.id,
        barber_id=barber_id,
        service_id=service_id,
        date=datetime.strptime(date, "%Y-%m-%d").date(),
        time=datetime.strptime(time, "%H:%M").time(),
        status="Pending",
        payment_status="Unpaid",
    )
    db.session.add(booking)
    db.session.commit()
    return redirect(url_for("booking.list_bookings", customer_email=email))


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
    response = {
        "page": page,
        "per_page": per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "data": bookings,
    }
    return jsonify(response)
