"""Auth module routes"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from ..extensions import login_manager
from app.extensions import db
from app.models.admin import Admin

auth_bp = Blueprint("auth", __name__)


# auth/routes.py  (already updated)
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.verify_password(password):
            login_user(admin)
            return redirect(request.args.get("next") or url_for("admin.dashboard"))
        flash("Invalid credentials")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@auth_bp.route("/create_admin", methods=["GET", "POST"])

def create_admin():
    """Create the first admin user if none exist."""
    # allow multiple admins – skip existence check
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        if not username or not email or not password:
            flash("All fields are required")
            return redirect(url_for("auth.create_admin"))
        if Admin.query.filter((Admin.username == username) | (Admin.email == email)).first():
            flash("Username or email already taken")
            return redirect(url_for("auth.create_admin"))
        # Hash the password and create the admin record
        admin = Admin(
            username=username,
            email=email,
            password_hash=Admin.hash_password(password),
        )
        db.session.add(admin)
        db.session.commit()
        flash("Admin user created successfully")
        login_user(admin)
        return redirect(url_for("admin.dashboard"))
    return render_template("auth/create_admin.html")
