"""Barber module routes (placeholder)."""

from flask import Blueprint

barber_bp = Blueprint("barber", __name__)

@barber_bp.route("/schedule")
def schedule():
    return "Barber schedule placeholder"