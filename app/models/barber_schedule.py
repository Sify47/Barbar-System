from app.extensions import db


class BarberSchedule(db.Model):
    __tablename__ = "barber_schedule"

    id = db.Column(db.Integer, primary_key=True)
    barber_id = db.Column(db.Integer, db.ForeignKey("barber.id"), nullable=False)
    day_of_week = db.Column(db.SmallInteger, nullable=False)  # 0=Mon ... 6=Sun
    open_time = db.Column(db.Time, nullable=False)
    close_time = db.Column(db.Time, nullable=False)
    is_closed = db.Column(db.Boolean, default=False)

    barber = db.relationship("Barber", back_populates="schedules")

    __table_args__ = (db.UniqueConstraint("barber_id", "day_of_week"),)


class BarberTimeOff(db.Model):
    __tablename__ = "barber_time_off"

    id = db.Column(db.Integer, primary_key=True)
    barber_id = db.Column(db.Integer, db.ForeignKey("barber.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    all_day = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    reason = db.Column(db.String(255))

    barber = db.relationship("Barber", back_populates="time_off")
