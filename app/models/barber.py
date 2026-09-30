from app.extensions import db


class Barber(db.Model):
    __tablename__ = "barber"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    # phone = db.Column(db.String(30))

    # ✅ back_populates بدل backref (مفيش تعارض)
    bookings = db.relationship(
        "Booking",
        back_populates="barber",
        lazy="dynamic",
    )
    # ✅ أضف دول
    schedules = db.relationship(
        "BarberSchedule",
        back_populates="barber",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    time_off = db.relationship(
        "BarberTimeOff",
        back_populates="barber",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def schedule_for(self, weekday):
        """Return the schedule row for a given weekday (0=Mon)."""
        for s in self.schedules:
            if s.day_of_week == weekday:
                return s
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            # "phone": self.phone,
        }
