"""Cashier module routes (placeholder)."""

from flask import Blueprint

cashier_bp = Blueprint("cashier", __name__)

@cashier_bp.route("/dashboard")
def dashboard():
    return "Cashier dashboard placeholder"