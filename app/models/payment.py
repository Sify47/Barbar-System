"""Payment model placeholder."""
from app.extensions import db
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'))
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Unpaid')