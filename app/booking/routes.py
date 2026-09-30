"""Booking module routes (placeholder)."""

from flask import Blueprint

booking_bp = Blueprint("booking", __name__)

@booking_bp.route("/create")
def create():
    return "Create booking placeholder"