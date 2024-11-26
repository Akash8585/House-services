from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_migrate import Migrate
from db import db
from models import User, Professional, Customer, Service, Request, Feedback, Notification  # Add Service and other models here
from forms import CustomerSignupForm, LoginForm, ProfessionalSignupForm
import os
from models import generate_unique_id
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'

csrf = CSRFProtect(app)
# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "instance", "service_platform.db")
if not os.path.exists(os.path.dirname(db_path)):
    os.makedirs(os.path.dirname(db_path))

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_TIME_LIMIT'] = 3600 

db.init_app(app)
migrate = Migrate(app, db)

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data.strip()
        password = form.password.data.strip()

        # Retrieve the user based on email
        user = User.query.filter_by(email=email).first()

        if user:
            # Debug: Print stored hash and input password for troubleshooting
            print(f"Stored Hash: {user._password}")
            print(f"Input Password: {repr(password)}")
            
            if user.verify_password(password):  # Verifying the password
                session['user_id'] = user.id
                session['role'] = user.role
                flash('Login successful!', 'success')

                # Redirect based on role
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user.role == 'professional':
                    return redirect(url_for('professional_dashboard'))
                elif user.role == 'customer':
                    return redirect(url_for('customer_dashboard'))
            else:
                # Debug: Log a message if password verification fails
                print("Password verification failed!")
                flash('Invalid credentials. Please check your email and password.', 'danger')
        else:
            # Debug: Log a message if user not found
            print(f"No user found with email: {email}")
            flash('Invalid credentials. Please check your email and password.', 'danger')

    return render_template('login.html', form=form)


@app.route('/professional_signup', methods=['GET', 'POST'])
def professional_signup():
    form = ProfessionalSignupForm()
    if form.validate_on_submit():
        new_professional = Professional(
            name=form.name.data,
            email=form.email.data,
            password=form.password.data,  # Uses the password setter
            phone_number=form.phone.data,
            service_type=form.service_type.data,
            experience=form.experience.data,
            address=form.address.data,
            pincode=form.pincode.data
        )
        db.session.add(new_professional)
        db.session.commit()
        flash('Professional account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('professional/professional_signup.html', form=form)

@app.route('/customer_signup', methods=['GET', 'POST'])
def customer_signup():
    form = CustomerSignupForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered.', 'danger')
        else:
            new_customer = Customer(
                name=form.name.data,
                email=form.email.data,
                password=form.password.data,  # Uses the password setter
                phone_number=form.phone.data,
                address=form.address.data,
                pincode=form.pincode.data
            )
            db.session.add(new_customer)
            db.session.commit()
            flash('Customer account created successfully!', 'success')
            return redirect(url_for('login'))
    return render_template('customer/customer_signup.html', form=form)

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    # Query data for dashboard
    professionals = Professional.query.all()
    customers = Customer.query.all()
    services = Service.query.all()
    requests = Request.query.all()
    all_users = User.query.all()

    for user in all_users:
             print(f"User ID: {user.id}, Role: {user.role}")

    # Count statistics
    total_professionals = len(professionals)
    total_customers = len(customers)
    total_requests = len(requests)
    pending_approvals = len([p for p in professionals if p.status == 'pending'])

    
    professional = None


    # Handle service addition via form submission
    if request.method == 'POST':
        service_name = request.form.get('service_name')
        service_description = request.form.get('description')
        price = request.form.get('base_price')
        duration = request.form.get('duration')

        if service_name and price and duration:
            new_service = Service(
                id=generate_unique_id(),
                service_name=service_name,
                service_description=service_description,
                price=float(price),
                duration=duration
            )
            db.session.add(new_service)
            db.session.commit()
            flash('New service added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))  # Refresh the page

        flash('Please fill out all required fields.', 'danger')

    return render_template(
        'admin/admin_dashboard.html',
        professionals=professionals,
        customers=customers,
        services=services,
        requests=requests,
        total_professionals=total_professionals,
        total_customers=total_customers,
        total_requests=total_requests,
        pending_approvals=pending_approvals,
        professional=professional
        
    )

@app.route('/delete_service/<id>', methods=['POST'])
def delete_service(id):
    # Retrieve the service by ID
    service = Service.query.get(id)
    if service:
        try:
            db.session.delete(service)  # Delete the service
            db.session.commit()
            flash(f'Service "{service.service_name}" has been deleted.', 'success')
        except Exception as e:
            db.session.rollback()  # Roll back in case of error
            flash(f'Failed to delete service: {str(e)}', 'danger')
    else:
        flash('Service not found.', 'danger')

    return redirect(url_for('admin_dashboard'))  # Redirect back to the admin dashboard
  # Redirect back to the admin dashboard
  # Redirect back to the admin dashboard
@app.route('/edit_service', methods=['POST'])
def edit_service():
    service_id = request.form.get('service_id')
    service = Service.query.get(service_id)

    if service:
        service.service_name = request.form.get('service_name')
        service.service_description = request.form.get('description')
        service.price = float(request.form.get('base_price'))
        service.duration = request.form.get('duration')

        try:
            db.session.commit()
            flash(f'Service "{service.service_name}" has been updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating service: {str(e)}', 'danger')
    else:
        flash('Service not found.', 'danger')

    return redirect(url_for('admin_dashboard'))




@app.route('/approve_professional/<id>', methods=['POST'])
def approve_professional(id):
    professional = Professional.query.get(id)
    if professional:
        professional.status = 'approved'
        db.session.commit()
        flash(f'Professional {professional.name} has been approved.', 'success')
    return redirect(url_for('admin_dashboard'))
@app.route('/reject_professional/<id>', methods=['POST'])
def reject_professional(id):
    professional = Professional.query.get(id)
    if professional:
        professional.status = 'rejected'
        db.session.commit()
        flash(f'Professional {professional.name} has been rejected.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/block_customer/<id>', methods=['POST'])
def block_customer(id):
    customer = Customer.query.get(id)
    if customer:
        customer.status = 'blocked'
        db.session.commit()
        flash(f'Customer {customer.name} has been blocked.', 'warning')
    else:
        flash('Customer not found!', 'danger')
    return redirect(url_for('admin_dashboard'))
    # Implement the logic for the admin search page
@app.route('/unblock_user/<id>', methods=['POST'])
def unblock_user(id):
    professional = Professional.query.get(id)
    if professional:
        professional.status = 'approved'  # or 'active', depending on your logic
        db.session.commit()
        flash('User unblocked successfully!', 'success')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('admin_dashboard'))
@app.route('/block_professional/<id>', methods=['POST'])
def block_professional(id):
    professional = Professional.query.get(id)
    if professional:
        professional.status = 'blocked'
        db.session.commit()
        flash(f'Professional {professional.name} has been blocked.', 'warning')
    else:
        flash('Professional not found!', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/unblock_customer', methods=['POST'])
def unblock_customer():
    customer_id = request.form.get('id')
    customer = Customer.query.get(customer_id)
    
    if customer:
        customer.status = 'active'
        db.session.commit()
        flash('Customer unblocked successfully!', 'success')
    else:
        flash('Customer not found!', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/show_professional_details', methods=['GET'])
def show_professional_details():
       pro_id = request.args.get('id')
       professional = Professional.query.get(pro_id)

       if not professional:
           flash('Professional not found!', 'danger')
           return redirect(url_for('admin_dashboard'))

       professionals = Professional.query.all()
       customers = Customer.query.all()
       services = Service.query.all()
       requests = Request.query.all()

       return render_template(
           'admin/admin_dashboard.html',
           professionals=professionals,
           customers=customers,
           services=services,
           requests=requests,
           total_professionals=len(professionals),
           total_customers=len(customers),
           total_requests=len(requests),
           pending_approvals=len([p for p in professionals if p.status == 'pending']),
           professional=professional,
           customer=None  # Ensure customer is defined
       )

@app.route('/show_customer_details', methods=['GET'])
def show_customer_details():
       customer_id = request.args.get('id')
       customer = Customer.query.get(customer_id)
       
       if not customer:
           flash('Customer not found', 'error')
           return redirect(url_for('admin_dashboard'))

       professionals = Professional.query.all()
       customers = Customer.query.all()
       services = Service.query.all()
       requests = Request.query.all()

       return render_template(
           'admin/admin_dashboard.html',
           professionals=professionals,
           customers=customers,
           services=services,
           requests=requests,
           total_professionals=len(professionals),
           total_customers=len(customers),
           total_requests=len(requests),
           pending_approvals=len([p for p in professionals if p.status == 'pending']),
           customer=customer,
           professional=None  # Ensure professional is defined
       )



@app.route('/admin_search')
def admin_search():
    # Implement the logic for the admin search page
    return render_template('admin/admin_search.html')

@app.route('/admin_summary')
def admin_summary():
    # Implement the logic for the admin search page
    return render_template('admin/admin_summary.html')

@app.route('/professional_dashboard')
def professional_dashboard():
    return render_template('professional/professional_dashboard.html')

@app.route('/customer_dashboard')
def customer_dashboard():
    return render_template('customer/customer_dashboard.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True)