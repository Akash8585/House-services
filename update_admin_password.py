# from app import app  # Import your Flask app instance
# from db import db  # Import your SQLAlchemy database instance
# from models import User  # Import your User model

# # Ensure app context for database operations
# with app.app_context():
#     # Fetch the admin user by email
#     user = User.query.filter_by(email="admin@example.com").first()
    
#     if user:
#         # Update the password hash
#         user._password = "pbkdf2:sha256:260000$bY33hHHUeG55fthY$aeef71dda2b7bf454d7cfbb24308ac77f7eaf1e00b29722ae0190fbdc9c0c5b8"  # Replace with the generated hash
#         db.session.commit()  # Commit the changes
#         print("Admin password updated successfully.")
#     else:
#         print("Admin user not found!")


from app import app  # Import your Flask app instance
from db import db  # Import your SQLAlchemy database instance
from models import User  # Import your User model

# Ensure app context for database operations
with app.app_context():
    # Fetch the admin user by email
    user = User.query.filter_by(email="jane.customer@example.com").first()
    
    if user:
        # Use the password property to hash the password safely
        user.password = "customer123"  # Replace with the new raw password
        db.session.commit()  # Commit the changes
        print("Customer password updated successfully.")
    else:
        print("Customer user not found!")
