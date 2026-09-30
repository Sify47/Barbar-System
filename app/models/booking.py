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

    # relationships
    customer = db.relationship('Customer', backref='bookings')
    barber = db.relationship('Barber', backref='bookings')
    service = db.relationship('Service', backref='bookings')

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "barber_id": self.barber_id,
            "service_id": self.service_id,
            "date": self.date.isoformat() if self.date else None,
            "time": self.time.isoformat() if self.time else None,
            "status": self.status,
            "payment_status": self.payment_status,
        }