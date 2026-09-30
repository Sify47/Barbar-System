"""Auth module routes (placeholder)."""

from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login():
    return "Login page placeholder"

# Allow accessing the auth module at both /auth and /auth/ (no trailing slash)
@auth_bp.route("/", strict_slashes=False)
def index():
    # Simple placeholder response. A real implementation could
    # redirect to the login page or render a template.
    return "Auth index placeholder – please use /auth/login"