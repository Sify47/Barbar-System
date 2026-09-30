from datetime import date
from app.extensions import db


class Coupon(db.Model):
    __tablename__ = "coupon"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    description = db.Column(db.String(255))
    discount_type = db.Column(db.Enum("percent", "fixed"), nullable=False)
    value = db.Column(db.Numeric(10, 2), nullable=False)
    min_amount = db.Column(db.Numeric(10, 2), default=0)
    max_uses = db.Column(db.Integer)
    used_count = db.Column(db.Integer, default=0)
    valid_from = db.Column(db.Date)
    valid_to = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)

    def is_valid(self, subtotal=0):
        today = date.today()
        if not self.is_active:
            return False, "Coupon is not active."
        if self.valid_from and today < self.valid_from:
            return False, "Coupon is not yet valid."
        if self.valid_to and today > self.valid_to:
            return False, "Coupon has expired."
        if self.max_uses and self.used_count >= self.max_uses:
            return False, "Coupon usage limit reached."
        if subtotal and subtotal < float(self.min_amount or 0):
            return (
                False,
                f"Minimum order for this coupon is ${float(self.min_amount):.2f}.",
            )
        return True, None

    def compute_discount(self, subtotal):
        if self.discount_type == "percent":
            return round(subtotal * float(self.value) / 100, 2)
        return min(float(self.value), subtotal)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "description": self.description,
            "discount_type": self.discount_type,
            "value": float(self.value),
            "min_amount": float(self.min_amount or 0),
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "is_active": self.is_active,
        }
