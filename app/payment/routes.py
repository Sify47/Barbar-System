"""Payment module routes (placeholder)."""

from flask import Blueprint

payment_bp = Blueprint("payment", __name__)

@payment_bp.route("/record")
def record():
    return "Record payment placeholder"