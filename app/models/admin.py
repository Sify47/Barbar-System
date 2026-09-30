# app/models/admin.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class Admin(UserMixin, db.Model):
    """
    Simple admin account model.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return f"<Admin {self.username}>"

    # ------------------------------------------------------------------
    # Password helpers
    # ------------------------------------------------------------------
    @staticmethod
    def hash_password(plain_text):
        """Return a salted hash of the given raw password using pbkdf2."""
        return generate_password_hash(plain_text, method='pbkdf2:sha256')

    def verify_password(self, plain_text):
        """Return True if the given password matches the stored hash."""
        return check_password_hash(self.password_hash, plain_text)
