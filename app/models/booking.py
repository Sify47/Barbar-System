"""Booking model placeholder."""
from app.extensions import db
from datetime import datetime

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    barber_id = db.Column(db.Integer, db.ForeignKey('barber.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    payment_status = db.Column(db.String(20), default='Unpaid')