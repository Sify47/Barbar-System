"""Entry point for running the Flask application.

This file follows the conventional pattern of creating the Flask app via
``app.create_app`` and then running the :class:`flask_socketio.SocketIO`
instance. It is intentionally lightweight so that the application can be
started with a simple ``python run.py`` command.
"""

from app import create_app
from app.extensions import socketio


app = create_app()

if __name__ == "__main__":
    # Default to port 5000; in production you would typically build a WSGI
    # interface and front end server (e.g., gunicorn + nginx).
    # In development environment we allow the unsafe Werkzeug server
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)