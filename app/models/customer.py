from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class Customer(db.Model):
    __tablename__ = "customer"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(255))

    # Relationship (already in place)
    bookings = db.relationship("Booking", back_populates="customer", lazy="selectin")

    # ---------- Auth helpers ----------
    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, raw)

    @property
    def has_account(self):
        return bool(self.password_hash)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
        }
