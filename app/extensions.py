from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO

# Database ORM
db = SQLAlchemy()

# Database migration utility
migrate = Migrate()

# Real-time communication
socketio = SocketIO()

__all__ = ["db", "migrate", "socketio"]