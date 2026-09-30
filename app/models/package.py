from app.extensions import db

# Association table: a Package contains many Services
package_services = db.Table(
    "package_services",
    db.Column("package_id", db.Integer, db.ForeignKey("package.id"), primary_key=True),
    db.Column("service_id", db.Integer, db.ForeignKey("service.id"), primary_key=True),
)


class Package(db.Model):
    __tablename__ = "package"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration = db.Column(db.Integer)  # total minutes (optional)

    # Relationship to services through the association table
    services = db.relationship(
        "Service",
        secondary=package_services,
        backref=db.backref("packages", lazy="dynamic"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price) if self.price is not None else None,
            "duration": self.duration,
            "services": [s.to_dict() for s in self.services],
        }
