from flask import Flask
from .extensions import db, migrate, socketio
from .config import DevelopmentConfig

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    # register blueprints
    try:
        from .auth.routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
    except Exception:
        pass
    try:
        from .customer.routes import customer_bp
        app.register_blueprint(customer_bp, url_prefix='/customer')
    except Exception:
        pass
    try:
        from .cashier.routes import cashier_bp
        app.register_blueprint(cashier_bp, url_prefix='/cashier')
    except Exception:
        pass
    try:
        from .barber.routes import barber_bp
        app.register_blueprint(barber_bp, url_prefix='/barber')
    except Exception:
        pass
    try:
        from .admin.routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
    except Exception:
        pass
    try:
        from .booking.routes import booking_bp
        app.register_blueprint(booking_bp, url_prefix='/booking')
    except Exception:
        pass
    try:
        from .payment.routes import payment_bp
        app.register_blueprint(payment_bp, url_prefix='/payment')
    except Exception:
        pass
    try:
        from .realtime.routes import realtime_bp
        app.register_blueprint(realtime_bp, url_prefix='/realtime')
    except Exception:
        pass

    # Home route
    @app.route("/")
    def index():
        return "Hello from Barber System"

    return app