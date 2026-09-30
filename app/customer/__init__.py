from flask import Blueprint

customer_bp = Blueprint("customer", __name__, url_prefix="/account")

from app.customer import routes  # noqa
