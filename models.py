import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
from db import db
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import ARRAY  # Use ARRAY for PostgreSQL
from sqlalchemy.dialects.sqlite import JSON  

# Function to generate unique IDs
def generate_unique_id():
    """Generate a unique 6-character ID with numbers and alphabets."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=6))


# User Model
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(6), primary_key=True, default=generate_unique_id, unique=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    _password = db.Column("password", db.String(500), nullable=False)
    address = db.Column(db.String(300), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)
    role = db.Column(db.String(50), nullable=False)  # Customer or Professional

    __mapper_args__ = {
    'polymorphic_identity': 'user',
    'polymorphic_on': role,  # This allows loading unknown roles without crashing
    }

    def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           print(f"User created/modified: ID={self.id}, Role={self.role}")

    # Password Hashing and Verification
    @property
    def password(self):
        raise AttributeError("Password is not readable!")

    @password.setter
    def password(self, password):
        self._password = generate_password_hash(password, method="pbkdf2:sha256")


    def verify_password(self, password):
        password = password.strip()

        print(f"Verifying password. Stored Hash: {self._password}, Input Password: {repr(password)}")
        match = check_password_hash(self._password, password)
        print(f"Password Match: {match}")
        return match


# Admin Model
class Admin(User):
    __tablename__ = 'admins'
    
    id = db.Column(db.String(6), db.ForeignKey('users.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }


# Professional Model
class Professional(User):
    __tablename__ = 'professionals'
    
    id = db.Column(db.String(6), db.ForeignKey('users.id'), primary_key=True)
    service_type = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='pending')  # Add status column

    __mapper_args__ = {
        'polymorphic_identity': 'professional',
    }


# Customer Model
class Customer(User):
    __tablename__ = 'customers'
    
    id = db.Column(db.String(6), db.ForeignKey('users.id'), primary_key=True)
    status = db.Column(db.String(50), default='active')

    __mapper_args__ = {
        'polymorphic_identity': 'customer',
    }

    # Hybrid property to calculate total requests dynamically
    @hybrid_property
    def total_requests(self):
        return len(self.requests)

    @total_requests.expression
    def total_requests(cls):
        return (
            db.session.query(func.count(Request.id))
            .filter(Request.customer_id == cls.id)
            .label("total_requests")
        )


# Service Model
# Service Model
class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.String(6), primary_key=True, default=generate_unique_id, unique=True)
    service_name = db.Column(db.String(100), nullable=False)
    service_description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float, nullable=True)  # Use Float if you need fractional hours # Add duration (only date) column

    # Relationship to Request without backref
  
    requests = db.relationship('Request', back_populates='service', lazy=True, passive_deletes=True)

    



# Request Model
# Request Model
class Request(db.Model):
    __tablename__ = 'requests'
    
    id = db.Column(db.String(6), primary_key=True, default=generate_unique_id, unique=True)
    customer_id = db.Column(db.String(6), db.ForeignKey('customers.id'), nullable=False)
    professional_id = db.Column(db.String(6), db.ForeignKey('professionals.id'), nullable=True)
    service_id = db.Column(db.String(6), db.ForeignKey('services.id', ondelete="SET NULL"), nullable=True)
    status = db.Column(db.String(50), nullable=False)  # Pending, In Progress, Completed
    request_date = db.Column(db.DateTime, nullable=False)
    completion_date = db.Column(db.DateTime, nullable=True)
    rejected_by = db.Column(db.JSON, default=list)  
    fee = db.Column(db.Float, nullable=True)

    # Define relationships
    professional = db.relationship('Professional', backref='requests')
    service = db.relationship('Service', back_populates='requests')
    customer = db.relationship('Customer', backref='requests')  
# Feedback Model
class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    id = db.Column(db.String(6), primary_key=True, default=generate_unique_id, unique=True)
    request_id = db.Column(db.String(6), db.ForeignKey('requests.id'), nullable=False)
    customer_id = db.Column(db.String(6), db.ForeignKey('customers.id'), nullable=False)
    professional_id = db.Column(db.String(6), db.ForeignKey('professionals.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    feedback_date = db.Column(db.DateTime, nullable=False)
      # Add this line

    customer = db.relationship("Customer", backref="feedbacks")
    professional = db.relationship("Professional", backref="feedbacks")
    request = db.relationship('Request', backref='feedbacks')  # Add this line


# Notification Model
class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.String(6), primary_key=True, default=generate_unique_id, unique=True)
    sender_id = db.Column(db.String(6), db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g., "Review Request", "Blocked User"
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    is_read = db.Column(db.Boolean, default=False)



