from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_migrate import Migrate
from db import db
from models import User, Professional, Customer, Service, Request, Feedback, Notification  # Add Service and other models here
from forms import CustomerSignupForm, LoginForm, ProfessionalSignupForm
import os
from models import generate_unique_id
from flask_wtf.csrf import CSRFProtect
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import io
import base64
from collections import defaultdict
from sqlalchemy import extract
from datetime import datetime


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

    return redirect(request.referrer or url_for('admin_dashboard'))  # Redirect back to the admin dashboard
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

    return redirect(request.referrer or url_for('admin_dashboard'))




@app.route('/approve_professional/<id>', methods=['POST'])
def approve_professional(id):
    professional = Professional.query.get(id)
    if professional:
        professional.status = 'approved'
        db.session.commit()
        flash(f'Professional {professional.name} has been approved.', 'success')
    return redirect(request.referrer or url_for('admin_dashboard'))  # Redirect back to the referring page (search)

@app.route('/reject_professional/<id>', methods=['POST'])
def reject_professional(id):
    professional = Professional.query.get(id)
    if professional:
        professional.status = 'rejected'
        db.session.commit()
        flash(f'Professional {professional.name} has been rejected.', 'danger')
    return redirect(request.referrer or url_for('admin_dashboard'))
@app.route('/block_professional/<id>', methods=['POST'])
def block_professional(id):
       professional = Professional.query.get(id)
       if professional:
           print(f"Blocking professional: ID={professional.id}, Current Status={professional.status}")
           professional.status = 'blocked'
           db.session.commit()
           print(f"Professional blocked: ID={professional.id}, New Status={professional.status}")
           flash(f'Professional {professional.name} has been blocked.', 'warning')
       else:
           flash('Professional not found!', 'danger')
       return redirect(request.referrer or url_for('admin_dashboard'))
@app.route('/unblock_user/<id>', methods=['POST'])
def unblock_user(id):
    professional = Professional.query.get(id)
    if professional:
        professional.status = 'approved'  # or 'active', depending on your logic
        db.session.commit()
        flash(f'Professional {professional.name} has been unblocked.', 'success')
    else:
        flash('Professional not found!', 'danger')
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/block_customer/<id>', methods=['POST'])
def block_customer(id):
       customer = Customer.query.get(id)
       if customer:
           customer.status = 'blocked'
           db.session.commit()
           flash(f'Customer {customer.name} has been blocked.', 'warning')
       else:
           flash('Customer not found!', 'danger')
       return redirect(request.referrer or url_for('admin_dashboard'))  

@app.route('/unblock_customer/<id>', methods=['POST'])
def unblock_customer(id):
       customer = Customer.query.get(id)
       if customer:
           customer.status = 'active'  # or whatever status indicates unblocked
           db.session.commit()
           flash(f'Customer {customer.name} has been unblocked.', 'success')
       else:
           flash('Customer not found!', 'danger')
       return redirect(request.referrer or url_for('admin_dashboard'))



@app.route('/show_professional_details', methods=['GET'])
def show_professional_details():
    pro_id = request.args.get('id')
    source_page = request.args.get('source', 'admin_dashboard')  # Determine source page
    professional = Professional.query.get(pro_id)

    if not professional:
        flash('Professional not found!', 'danger')
        return redirect(url_for(source_page))  # Redirect back to the source page

    professionals = Professional.query.all()
    customers = Customer.query.all()
    services = Service.query.all()
    requests = Request.query.all()

    entity = 'professionals'

    return render_template(
        f'admin/{source_page}.html',  # Render the correct page
        professionals=professionals,
        customers=customers,
        services=services,
        requests=requests,
        total_professionals=len(professionals),
        total_customers=len(customers),
        total_requests=len(requests),
        pending_approvals=len([p for p in professionals if p.status == 'pending']),
        professional=professional,
        customer=None,
        service_request=None,
        source_page=source_page,
        entity=entity,
        status=status,
        search_query=search_query,
        filtered_data=filtered_data,
        modal_item=modal_item  # Pass source_page to the template
    )




@app.route('/show_customer_details', methods=['GET'])
def show_customer_details():
    customer_id = request.args.get('id')
    source_page = request.args.get('source', 'admin_dashboard')  # Determine source page
    customer = Customer.query.get(customer_id)

    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for(source_page))  # Redirect back to the source page

    professionals = Professional.query.all()
    customers = Customer.query.all()
    services = Service.query.all()
    requests = Request.query.all()

    return render_template(
        f'admin/{source_page}.html',  # Render the correct page
        professionals=professionals,
        customers=customers,
        services=services,
        requests=requests,
        total_professionals=len(professionals),
        total_customers=len(customers),
        total_requests=len(requests),
        pending_approvals=len([p for p in professionals if p.status == 'pending']),
        customer=customer,
        professional=None,
        service_request=None,
        source_page=source_page
    )


@app.route('/show_service_request_details', methods=['GET'])
def show_service_request_details():
    req_id = request.args.get('id')
    source_page = request.args.get('source', 'admin_dashboard')  # Determine source page
    service_request = Request.query.get(req_id)

    if not service_request:
        flash('Service request not found!', 'danger')
        return redirect(url_for(source_page))  # Redirect back to the source page

    # Explicitly handle missing relationships
    customer_name = service_request.customer.name if service_request.customer else "Unknown"
    professional_name = service_request.professional.name if service_request.professional else "None"
    service_name = service_request.service.service_name if service_request.service else "N/A"

    professionals = Professional.query.all()
    customers = Customer.query.all()
    services = Service.query.all()
    requests = Request.query.all()

    return render_template(
        f'admin/{source_page}.html',  # Render the correct page
        professionals=professionals,
        customers=customers,
        services=services,
        requests=requests,
        total_professionals=len(professionals),
        total_customers=len(customers),
        total_requests=len(requests),
        pending_approvals=len([p for p in professionals if p.status == 'pending']),
        service_request=service_request,
        customer_name=customer_name,
        professional_name=professional_name,
        service_name=service_name,
        professional=None,
        customer=None,
        source_page=source_page
    )




@app.route('/admin_search', methods=['GET'])
def admin_search():
    entity = request.args.get('entity', 'services')  # Default to services
    status = request.args.get('status', '')
    search_query = request.args.get('search_query', '')
    id_filter = request.args.get('id', None)

    filtered_data = []

    if entity == 'services':
        query = Service.query
        if search_query:
            query = query.filter(
                Service.service_name.contains(search_query) |
                Service.service_description.contains(search_query)
            )
        filtered_data = query.all()

    elif entity == 'service_requests':
        query = Request.query
        if search_query:
            query = query.filter(
                Request.id.contains(search_query) |
                Request.customer.has(Customer.name.contains(search_query))
            )
        if status:
            query = query.filter_by(status=status)
        filtered_data = query.all()

    elif entity == 'professionals':
        query = Professional.query
        if search_query:
            query = query.filter(
                Professional.name.contains(search_query) |
                Professional.service_type.contains(search_query)
            )
        if status:
            query = query.filter_by(status=status)
        filtered_data = query.all()

    elif entity == 'customers':
        query = Customer.query
        if search_query:
            query = query.filter(
                Customer.name.contains(search_query) |
                Customer.address.contains(search_query)
            )
        if status:
            query = query.filter_by(status=status)
        filtered_data = query.all()

    # If viewing a specific ID (to show modal)
    modal_item = None
    if id_filter:
        if entity == 'service_requests':
            modal_item = Request.query.get(id_filter)
        elif entity == 'professionals':
            modal_item = Professional.query.get(id_filter)
        elif entity == 'customers':
            modal_item = Customer.query.get(id_filter)

    return render_template(
        'admin/admin_search.html',
        entity=entity,
        status=status,
        search_query=search_query,
        filtered_data=filtered_data,
        modal_item=modal_item
    )



# Helper function to generate charts
import numpy as np

def generate_chart(data, chart_type, title, filename):
    if not data or all(value == 0 for value in data.values()):
        # Create an empty image if data is empty or all values are zero
        plt.figure(figsize=(6, 4))
        plt.text(0.5, 0.5, "No data available", ha='center', va='center', fontsize=14, alpha=0.6)
        plt.title(title)
        plt.axis('off')
        filepath = os.path.join("static/charts", filename)
        plt.savefig(filepath, bbox_inches="tight")
        plt.close()
        return f"static/charts/{filename}"

    # Filter out NaN or zero values
    valid_data = {k: v for k, v in data.items() if not np.isnan(v) and v > 0}

    plt.figure(figsize=(6, 4))
    if chart_type == "pie":
        plt.pie(valid_data.values(), labels=valid_data.keys(), autopct="%1.1f%%", startangle=140)
        plt.title(title)
    elif chart_type == "bar":
        plt.bar(valid_data.keys(), valid_data.values(), color="skyblue")
        plt.title(title)
        plt.xticks(rotation=45, ha="right")
    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")

    filepath = os.path.join("static/charts", filename)
    plt.savefig(filepath, bbox_inches="tight")
    plt.close()
    return f"static/charts/{filename}"


@app.route("/admin_summary")
def admin_summary():
    os.makedirs("static/charts", exist_ok=True)

    # Query data
    total_professionals = Professional.query.count()
    total_customers = Customer.query.count()
    total_requests = Request.query.count()
    pending_approvals = Professional.query.filter_by(status="pending").count()

    # Service category distribution
    service_category_distribution = {
        service.service_name: len(service.requests) for service in Service.query.all()
    }
    service_category_chart = generate_chart(
        service_category_distribution, "pie", "Service Categories Distribution", "service_category.png"
    )

    # Service requests by month
    months_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    service_requests_by_month = {
        month: Request.query.filter(extract("month", Request.request_date) == idx + 1).count()
        for idx, month in enumerate(months_order)
    }
    requests_by_month_chart = generate_chart(
        service_requests_by_month, "bar", "Service Requests by Month", "requests_by_month.png"
    )

    # Professional status distribution
    professional_status_distribution = {
        "Approved": Professional.query.filter_by(status="approved").count(),
        "Pending": Professional.query.filter_by(status="pending").count(),
        "Blocked": Professional.query.filter_by(status="blocked").count(),
    }
    professional_status_chart = generate_chart(
        professional_status_distribution, "pie", "Professional Status Distribution", "professional_status.png"
    )

    # Service request status distribution
    service_request_status_distribution = {
        "Pending": Request.query.filter_by(status="Pending").count(),
        "In Progress": Request.query.filter_by(status="In Progress").count(),
        "Completed": Request.query.filter_by(status="Completed").count(),
    }
    service_request_status_chart = generate_chart(
        service_request_status_distribution, "pie", "Service Request Status", "service_request_status.png"
    )

    return render_template(
        "admin/admin_summary.html",
        total_professionals=total_professionals,
        total_customers=total_customers,
        pending_approvals=pending_approvals,
        total_requests=total_requests,
        service_category_distribution=service_category_distribution,
        service_requests_by_month=service_requests_by_month,
        professional_status_distribution=professional_status_distribution,
        service_request_status_distribution=service_request_status_distribution,
        charts={
            "service_category": service_category_chart,
            "requests_by_month": requests_by_month_chart,
            "professional_status": professional_status_chart,
            "service_request_status": service_request_status_chart,
        },
    )









@app.route('/professional_dashboard')
def professional_dashboard():
    # Query data for the professional dashboard
    professional_id = session.get('user_id')  # Assuming the professional's ID is stored in the session
    professional = Professional.query.get(professional_id)
    
    # Fetch service requests related to the professional
    requested_services = Request.query.filter_by(professional_id=professional_id, status='pending').all()
    accepted_services = Request.query.filter_by(professional_id=professional_id, status='in progress').all()
    closed_services = Request.query.filter_by(professional_id=professional_id, status='closed').all()

    return render_template(
        'professional/professional_dashboard.html',
        professional=professional,
        requested_services=requested_services,
        accepted_services=accepted_services,
        closed_services=closed_services
    )

@app.route('/customer_dashboard')
def customer_dashboard():
    return render_template('customer/customer_dashboard.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True)