# app/__init__.py
from flask import Flask, render_template
from .extensions import db, migrate, socketio, login_manager
from .config import DevelopmentConfig

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    login_manager.init_app(app)  # added login_manager initialization

    # ------------------------------------------------------------------
    # Register blueprints
    # ------------------------------------------------------------------
    from .auth.routes import auth_bp
    from .customer.routes import customer_bp
    from .cashier.routes import cashier_bp
    from .barber.routes import barber_bp
    from .admin.routes import admin_bp
    from .booking.routes import booking_bp
    from .payment.routes import payment_bp
    from .realtime.routes import realtime_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(customer_bp, url_prefix="/customer")
    app.register_blueprint(cashier_bp, url_prefix="/cashier")
    app.register_blueprint(barber_bp, url_prefix="/barber")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(booking_bp, url_prefix="/booking")
    app.register_blueprint(payment_bp, url_prefix="/payment")
    app.register_blueprint(realtime_bp, url_prefix="/realtime")

    # ------------------------------------------------------------------
    # Login manager user loader
    # ------------------------------------------------------------------
    from .models.admin import Admin

    @login_manager.user_loader
    def load_user(user_id):
        # Try Admin first
        return Admin.query.get(int(user_id))

    # ------------------------------------------------------------------
    # Home route
    # ------------------------------------------------------------------
    @app.route("/")
    def index():
        from app.models.barber import Barber
        from app.models.service import Service
        barbers = Barber.query.all()
        services = Service.query.all()
        return render_template("index.html", barbers=barbers, services=services)

    return app
