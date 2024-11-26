import random
from datetime import datetime, timedelta
from faker import Faker
from werkzeug.security import generate_password_hash
from db import db
from models import User, Admin, Professional, Customer, Service, Request, Feedback, Notification

fake = Faker()

def hash_password(password):
    return generate_password_hash(password, method="pbkdf2:sha256")

def seed_users():
    # Create an admin user
    admin = Admin(
    id="ADMIN1",
    name="Admin User",
    email="admin@example.com",
    password=generate_password_hash("admin123", method="pbkdf2:sha256"),
    role="admin"
)
    db.session.add(admin)
    db.session.commit()

    # Create professionals
    for _ in range(40):
        professional = Professional(
            id=fake.unique.uuid4()[:6].upper(),
            name=fake.name(),
            email=fake.email(),
            password=generate_password_hash(fake.password()),
            address=fake.address(),
            pincode=fake.postcode(),
            phone_number=fake.phone_number(),
            role="professional",
            service_type=random.choice(["Plumbing", "Electrical", "Cleaning", "Painting"]),
            experience=random.randint(1, 20),
            status=random.choice(["pending", "approved", "blocked"])
        )
        db.session.add(professional)

    # Create customers
    for _ in range(60):
        customer = Customer(
            id=fake.unique.uuid4()[:6].upper(),
            name=fake.name(),
            email=fake.email(),
            password=generate_password_hash(fake.password()),
            address=fake.address(),
            pincode=fake.postcode(),
            phone_number=fake.phone_number(),
            role="customer"
        )
        db.session.add(customer)

    db.session.commit()

def seed_services():
    services = [
        {"name": "Plumbing Service", "description": "Fixing leaks and plumbing issues", "price": 100, "duration": 2},
        {"name": "Electrical Repair", "description": "Repairing electrical appliances", "price": 150, "duration": 3},
        {"name": "House Cleaning", "description": "Comprehensive house cleaning", "price": 120, "duration": 4},
        {"name": "Painting Service", "description": "Interior and exterior painting", "price": 200, "duration": 5},
    ]

    for service in services:
        db.session.add(Service(
            id=fake.unique.uuid4()[:6].upper(),
            service_name=service["name"],
            service_description=service["description"],
            price=service["price"],
            duration=service["duration"]  # Ensure duration is included
        ))

    db.session.commit()

def seed_requests():
    # Fetch customers and professionals
    customers = Customer.query.all()
    professionals = Professional.query.filter_by(status="approved").all()  # Only approved professionals
    services = Service.query.all()

    for _ in range(50):
        customer = random.choice(customers)
        service = random.choice(services)

        # Assign professional 50% of the time
        assign_professional = random.choice([True, False])
        professional = random.choice(professionals) if assign_professional and professionals else None

        request_date = fake.date_this_year()

        # Set request status
        status = "Pending" if not professional else random.choice(["In Progress", "Completed"])
        completion_date = None
        if status == "Completed":
            completion_date = request_date + timedelta(days=random.randint(1, 10))

        db.session.add(Request(
            id=fake.unique.uuid4()[:6].upper(),
            customer_id=customer.id,
            professional_id=professional.id if professional else None,
            service_id=service.id,
            status=status,
            request_date=request_date,
            completion_date=completion_date
        ))

    db.session.commit()

def seed_feedbacks():
    # Fetch completed requests
    completed_requests = Request.query.filter_by(status="Completed").all()

    for request in completed_requests:
        db.session.add(Feedback(
            id=fake.unique.uuid4()[:6].upper(),
            request_id=request.id,
            customer_id=request.customer_id,
            professional_id=request.professional_id,
            rating=random.randint(1, 5),
            comments=fake.sentence(),
            feedback_date=request.completion_date + timedelta(days=random.randint(1, 3))
        ))

    db.session.commit()

def seed_notifications():
    users = User.query.all()

    for _ in range(20):
        sender = random.choice(users)
        db.session.add(Notification(
            id=fake.unique.uuid4()[:6].upper(),
            sender_id=sender.id,
            type=random.choice(["Review Request", "Blocked User"]),
            message=fake.sentence(),
            timestamp=datetime.utcnow(),
            is_read=random.choice([True, False])
        ))

    db.session.commit()

def seed_database():
    seed_users()
    seed_services()
    seed_requests()
    seed_feedbacks()
    seed_notifications()
    print("Database seeded successfully!")

if __name__ == "__main__":
    from app import app  # Import app from app.py
    with app.app_context():
        db.create_all()  # Ensure tables are created
        seed_database()
