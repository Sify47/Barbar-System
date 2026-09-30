"""Barber model placeholder."""
from app.extensions import db

class Barber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    specialty = db.Column(db.String(120))