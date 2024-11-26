from app import app  # Your Flask app import
from db import db
from models import User

with app.app_context():  # Ensure app context is active
    user = User.query.filter_by(email="admin@example.com").first()
    if user:
        print(f"Stored Hash in Database: {user._password}")
    else:
        print("Admin user not found!")
