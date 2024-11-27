from app import app, db  # Import your Flask app and SQLAlchemy instance
from models import User, Customer, Professional, Request  # Import necessary models

with app.app_context():  # Create an application context
    user_id = 'F8AB19'  # ID of the user to delete

    # Fetch the user
    user = User.query.get(user_id)

    if user:
        print(f"User found: {user.name}, Role: {user.role}")

        # Check user role and delete related entries if necessary
        if user.role == 'customer':
            # Delete all requests associated with the customer
            db.session.query(Request).filter_by(customer_id=user_id).delete(synchronize_session=False)
            # Delete customer entry
            db.session.query(Customer).filter_by(id=user_id).delete(synchronize_session=False)

        elif user.role == 'professional':
            # Delete all requests associated with the professional
            db.session.query(Request).filter_by(professional_id=user_id).delete(synchronize_session=False)
            # Delete professional entry
            db.session.query(Professional).filter_by(id=user_id).delete(synchronize_session=False)

        # Finally, delete the user entry
        db.session.delete(user)
        db.session.commit()
        print(f"User with ID {user_id} and all related records deleted successfully.")
    else:
        print(f"No user found with ID {user_id}.")
