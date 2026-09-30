"""Customer module routes (placeholder)."""

from flask import Blueprint

customer_bp = Blueprint("customer", __name__)

@customer_bp.route("/profile")
def profile():
    return "Customer profile placeholder"