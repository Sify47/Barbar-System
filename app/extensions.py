# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_login import LoginManager

# ------------------------------------------------------------------
# Database ORM
# ------------------------------------------------------------------
db = SQLAlchemy()

# ------------------------------------------------------------------
# Database migration utility
# ------------------------------------------------------------------
migrate = Migrate()

# ------------------------------------------------------------------
# Real‑time communication
# ------------------------------------------------------------------
socketio = SocketIO()

# ------------------------------------------------------------------
# Authentication
# ------------------------------------------------------------------
login_manager = LoginManager()
login_manager.login_view = "auth.login"

__all__ = ["db", "migrate", "socketio", "login_manager"]
