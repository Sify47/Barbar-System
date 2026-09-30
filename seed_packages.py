"""One-time seeder for example packages."""

from app import create_app
from app.extensions import db
from app.models.package import Package
from app.models.service import Service

app = create_app()

with app.app_context():
    # Look up existing services by name (adjust names to match your DB)
    haircut = Service.query.filter_by(name="Haircut").first()
    beard = Service.query.filter_by(name="Beard Trim").first()
    shave = Service.query.filter_by(name="Classic Shave").first()
    wash = Service.query.filter_by(name="Hair Wash").first()

    packages_data = [
        {
            "name": "The Gentleman",
            "description": "A timeless combination for the modern man.",
            "price": 45.00,
            "duration": 60,
            "services": [s for s in [haircut, beard] if s],
        },
        {
            "name": "The Royal Treatment",
            "description": "Full grooming experience — cut, shave, and wash.",
            "price": 70.00,
            "duration": 90,
            "services": [s for s in [haircut, shave, wash] if s],
        },
        {
            "name": "Quick Refresh",
            "description": "In and out — just the essentials.",
            "price": 25.00,
            "duration": 30,
            "services": [s for s in [haircut] if s],
        },
    ]

    for data in packages_data:
        existing = Package.query.filter_by(name=data["name"]).first()
        if existing:
            continue
        pkg = Package(
            name=data["name"],
            description=data["description"],
            price=data["price"],
            duration=data["duration"],
        )
        pkg.services = data["services"]
        db.session.add(pkg)

    db.session.commit()
    print("Packages seeded ✅")
