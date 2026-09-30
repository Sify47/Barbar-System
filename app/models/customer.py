"""Customer model placeholder."""
from app.extensions import db

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True)
    # optional password for account, nullable until set
    password_hash = db.Column(db.String(128), nullable=True)