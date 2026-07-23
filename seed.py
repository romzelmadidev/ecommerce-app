from werkzeug.security import generate_password_hash
from models import db, User

def seed_users(app):
    with app.app_context():
        db.create_all()

        sample_users = [
            {
                "username": "john",
                "password": generate_password_hash("password123"),
                "first_name": "John",
                "last_name": "Doe",
                "acct_number": "10000001"
            },
            {
                "username": "jane",
                "password": generate_password_hash("password123"),
                "first_name": "Jane",
                "last_name": "Smith",
                "acct_number": "10000002"
            },
            {
                "username": "alice",
                "password": generate_password_hash("password123"),
                "first_name": "Alice",
                "last_name": "Johnson",
                "acct_number": "10000003"
            }
        ]

        seeded_count = 0

        for item in sample_users:
            existing = User.query.filter_by(username=item["username"]).first()

            if not existing:
                db.session.add(User(**item))
                seeded_count += 1

        db.session.commit()

        print(f"[SEED] Added {seeded_count} users.")

