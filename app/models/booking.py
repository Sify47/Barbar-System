from app.extensions import db

# Many-to-many: booking ↔ service
booking_services = db.Table(
    "booking_services",
    db.Column("booking_id", db.Integer, db.ForeignKey("booking.id"), primary_key=True),
    db.Column("service_id", db.Integer, db.ForeignKey("service.id"), primary_key=True),
)


class Booking(db.Model):
    __tablename__ = "booking"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    barber_id = db.Column(db.Integer, db.ForeignKey("barber.id"), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey("package.id"), nullable=True)

    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    coupon_id        = db.Column(db.Integer, db.ForeignKey("coupon.id"), nullable=True)
    discount_amount  = db.Column(db.Numeric(10, 2), default=0)

    status = db.Column(db.String(30), default="Pending")
    payment_status = db.Column(db.String(30), default="Unpaid")

    # ============ Relationships ============
    customer = db.relationship(
        "Customer",
        back_populates="bookings",   # ✅ بدل lazy="joined" بس
        lazy="joined",
    )

    barber = db.relationship(
        "Barber",
        back_populates="bookings",
        lazy="joined",
    )

    services = db.relationship(
        "Service",
        secondary=booking_services,
        backref=db.backref("bookings", lazy="dynamic"),
        lazy="selectin",
    )
    package = db.relationship("Package", lazy="selectin")
    coupon = db.relationship("Coupon", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "customer": (
                {
                    "id": self.customer.id,
                    "name": self.customer.name,
                    "phone": self.customer.phone,
                    "email": self.customer.email,
                }
                if self.customer
                else None
            ),
            "barber_id": self.barber_id,
            "barber": (
                {"id": self.barber.id, "name": self.barber.name}
                if self.barber
                else None
            ),
            "package_id": self.package_id,
            "package": (
                {
                    "id": self.package.id,
                    "name": self.package.name,
                    "price": float(self.package.price),
                }
                if self.package
                else None
            ),
            "services": [
                {"id": s.id, "name": s.name, "price": float(s.price)}
                for s in self.services
            ],
            "date": self.date.isoformat() if self.date else None,
            "time": self.time.strftime("%H:%M") if self.time else None,
            "status": self.status,
            "payment_status": self.payment_status,
            "total": float(self.compute_total()),
        }


    def compute_subtotal(self):
        if self.package:
            return float(self.package.price or 0)
        return sum(float(s.price or 0) for s in self.services)


    def compute_total(self):
        return max(0, self.compute_subtotal() - float(self.discount_amount or 0))
