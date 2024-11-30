from flask import Flask, render_template, request, redirect, url_for, flash, session, current_app
from flask_migrate import Migrate
from db import db
from models import User, Professional, Customer, Service, Request, Feedback, Notification, db  # Add Service and other models here
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
import numpy as np
import json


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
                
                if user.status == 'blocked':
                    return redirect(url_for('blocked_user_page'))
                
                if user.role == 'professional':
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
    services = Service.query.with_entities(Service.service_name).all()
    service_names = [service.service_name for service in services]

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

        if new_professional.status == 'pending':
            notification = Notification(
                sender_id=new_professional.id,
                type='New Professional Registration',
                message=f'A new professional {new_professional.name} ({new_professional.email}) has registered and is pending approval.',
                timestamp=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()

        flash('Professional account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('professional/professional_signup.html', form=form, service_names=service_names)

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

@app.route('/blocked_user_page', methods=['GET', 'POST'])
def blocked_user_page():
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if not user or user.status != 'blocked':
        return redirect(url_for('login'))  # Redirect if not blocked or not logged in

    if request.method == 'POST':
        # Handle request for review
        new_notification = Notification(
            sender_id=user.id,
            type='Review Request',
            message=f"User {user.name} (ID: {user.id}) is requesting an account review.",
            timestamp=datetime.utcnow(),
            is_read=False
        )
        db.session.add(new_notification)
        db.session.commit()
        flash('Your request has been sent to the admin.', 'success')

    return render_template('blocked_user.html', user=user)


@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    # Query data for dashboard
    professionals = Professional.query.all()
    customers = Customer.query.all()
    services = Service.query.all()

    notifications = Notification.query.order_by(Notification.timestamp.desc()).all()
    unread_count = sum(1 for notification in notifications if not notification.is_read)

    # Group service requests
    requests = Request.query.all()
    grouped_requests = {
        "requested": [r for r in requests if r.status == "requested"],
        "closed": [r for r in requests if r.status == "closed"],
        "accepted": [
            r for r in requests if r.status in {"accepted", "in progress", "review pending", "pending", "assigned"}
        ],
    }

    # Count statistics
    total_professionals = len(professionals)
    total_customers = len(customers)
    total_requests = len(requests)
    pending_approvals = len([p for p in professionals if p.status == "pending"])

    professional = None

    # Handle service addition via form submission
    if request.method == "POST":
        service_name = request.form.get("service_name")
        service_description = request.form.get("description")
        price = request.form.get("base_price")
        duration = request.form.get("duration")

        if service_name and price and duration:
            new_service = Service(
                id=generate_unique_id(),
                service_name=service_name,
                service_description=service_description,
                price=float(price),
                duration=duration,
            )
            db.session.add(new_service)
            db.session.commit()
            flash("New service added successfully!", "success")
            return redirect(url_for("admin_dashboard"))  # Refresh the page

        flash("Please fill out all required fields.", "danger")

    return render_template(
        "admin/admin_dashboard.html",
        professionals=professionals,
        customers=customers,
        services=services,
        requests=requests,
        grouped_requests=grouped_requests,
        total_professionals=total_professionals,
        total_customers=total_customers,
        total_requests=total_requests,
        pending_approvals=pending_approvals,
        professional=professional,
        notifications=notifications,
        unread_count=unread_count
    )

@app.route('/mark_notifications_read', methods=['POST'])
def mark_notifications_read():
    print("Route /mark_notifications_read called")
    unread_notifications = Notification.query.filter_by(is_read=False).all()
    print(f"Unread notifications count: {len(unread_notifications)}")
    for notification in unread_notifications:
        notification.is_read = True
        print(f"Marking notification {notification.id} as read")
    db.session.commit()
    return '', 204



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
        # Delete the professional directly
        db.session.delete(professional)
        db.session.commit()
        flash(f'Professional {professional.name} has been rejected and removed.', 'success')
    else:
        flash('Professional not found.', 'danger')
    
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
    status = request.args.get('status', 'default_status')
    search_query = request.args.get('search_query', '')
    filtered_data = [] 
    modal_item = None 

    if not professional:
        flash('Professional not found!', 'danger')
        return redirect(url_for(source_page))  # Redirect back to the source page
    
    notifications = Notification.query.order_by(Notification.timestamp.desc()).all()
    unread_count = sum(1 for notification in notifications if not notification.is_read)


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
        modal_item=modal_item,  # Pass source_page to the template
        unread_count=unread_count
    )
    




@app.route('/show_customer_details', methods=['GET'])
def show_customer_details():
    customer_id = request.args.get('id')
    source_page = request.args.get('source', 'admin_dashboard')  # Determine source page
    customer = Customer.query.get(customer_id)

    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for(source_page)) 
    
    notifications = Notification.query.order_by(Notification.timestamp.desc()).all()
    unread_count = sum(1 for notification in notifications if not notification.is_read) # Redirect back to the source page

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
        source_page=source_page,
        unread_count=unread_count
    
    )


@app.route('/show_service_request_details', methods=['GET'])
def show_service_request_details():
    req_id = request.args.get('id')
    source_page = request.args.get('source', 'admin_dashboard')  # Determine source page
    service_request = Request.query.get(req_id)

    if not service_request:
        flash('Service request not found!', 'danger')
        return redirect(url_for(source_page))
    
    notifications = Notification.query.order_by(Notification.timestamp.desc()).all()
    unread_count = sum(1 for notification in notifications if not notification.is_read)  # Redirect back to the source page

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
        source_page=source_page,
        unread_count=unread_count
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
        if status == 'accepted':
            query = query.filter(Request.status.notin_(['requested', 'closed']))
        elif status:
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





def generate_chart(data, chart_type, title, filename):
    """
    Generate a chart using matplotlib, save it as an image, and return the file path.

    Args:
        data (dict): Data for the chart, with keys as labels and values as numbers.
        chart_type (str): The type of chart to generate ('pie', 'bar').
        title (str): The title of the chart.
        filename (str): The name of the output file to save in 'static/charts'.

    Returns:
        str: File path of the saved chart image.
    """
    # Ensure the charts directory exists
    charts_dir = "static/charts"
    os.makedirs(charts_dir, exist_ok=True)

    # Handle the case where data is empty or all values are zero
    if not data or all(value == 0 for value in data.values()):
        plt.figure(figsize=(6, 4))
        plt.text(0.5, 0.5, "No data available", ha='center', va='center', fontsize=14, alpha=0.6)
        plt.title(title)
        plt.axis('off')  # Hide axes
        filepath = os.path.join(charts_dir, filename)
        plt.savefig(filepath, bbox_inches="tight")
        plt.close()
        return filepath

    # Filter out invalid data (e.g., NaN or zero values)
    valid_data = {k: v for k, v in data.items() if not np.isnan(v) and v > 0}

    # Generate the chart
    plt.figure(figsize=(6, 4))
    if chart_type == "pie":
        plt.pie(valid_data.values(), labels=valid_data.keys(), autopct="%1.1f%%", startangle=140)
        plt.title(title)
    elif chart_type == "bar":
        plt.bar(valid_data.keys(), valid_data.values(), color="skyblue")
        plt.title(title)
        plt.xticks(rotation=45, ha="right")  # Rotate x-axis labels for better readability
    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")

    # Save the chart as an image
    filepath = os.path.join(charts_dir, filename)
    plt.savefig(filepath, bbox_inches="tight")
    plt.close()

    return filepath



@app.route("/admin_summary")
def admin_summary():
    os.makedirs("static/charts", exist_ok=True)  # Ensure charts directory exists

    # Query data
    total_professionals = Professional.query.count()
    total_customers = Customer.query.count()
    total_requests = Request.query.count()
    pending_approvals = Professional.query.filter_by(status="pending").count()

    # Service category distribution
    services = Service.query.all()
    service_category_distribution = {
        service.service_name: Request.query.filter_by(service_id=service.id).count() for service in services
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
        "requested": Request.query.filter_by(status="requested").count(),
        "accepted": Request.query.filter(
            Request.status.in_(["accepted", "in progress", "review pending", "pending", "assigned"])
        ).count(),
        "closed": Request.query.filter_by(status="closed").count(),
        "canceled": Request.query.filter_by(status="canceled").count(),
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
    professional_id = session.get('user_id')
    professional = db.session.get(Professional, professional_id)

    if not professional:
        flash('Professional not found.', 'danger')
        return redirect(url_for('login'))

    # Fetch all requested services that match the professional's service type
    all_requested_services = Request.query.filter(
        Request.status == 'requested',
        Request.professional_id.is_(None),
        Request.service.has(Service.service_name == professional.service_type)  # Filter by service type
    ).all()

    # Filter out requests rejected by this professional
    requested_services = [
        request for request in all_requested_services
        if professional_id not in (request.rejected_by or [])
    ]

    # Accepted services
    accepted_services = Request.query.filter(
        Request.professional_id == professional_id,
        Request.status.in_(['pending', 'in progress'])
    ).all()

    # Closed services
    closed_services = Request.query.filter(
        Request.professional_id == professional_id,
        Request.status.in_(['review pending', 'closed'])
    ).all()

    return render_template(
        'professional/professional_dashboard.html',
        professional=professional,
        requested_services=requested_services,
        accepted_services=accepted_services,
        closed_services=closed_services
    )








@app.route('/professional_search', methods=['GET'])
def professional_search():
    # Get the logged-in professional ID
    professional_id = session.get('user_id')
    professional = Professional.query.get(professional_id)

    # Retrieve filters from request
    status = request.args.get('status', '')
    search_query = request.args.get('search_query', '')

    # Query for service requests assigned to the logged-in professional
    query = Request.query.filter_by(professional_id=professional_id)

    if status:
        query = query.filter_by(status=status)  # Filter by status if provided

    if search_query:
        query = query.filter(
        Request.customer.has(Customer.name.contains(search_query)) |
        Request.service.has(Service.service_name.contains(search_query)) |
        Request.request_date.contains(search_query) |
        Request.customer.has(Customer.pincode.contains(search_query))
    )  # Filter by customer name, service name, request date, or pincode  # Filter by customer or service name

    filtered_data = query.all()

    return render_template(
        'professional/professional_search.html',
        filtered_data=filtered_data,
        status=status,
        search_query=search_query,
        professional=professional 
    )



@app.route("/professional_summary")
def professional_summary():
    professional_id = session.get("user_id")  # Assuming professional's ID is stored in session
    professional = Professional.query.get(professional_id)

    # Statistics
    completed_services = Request.query.filter_by(professional_id=professional_id, status="closed").count()
    accepted_services = Request.query.filter_by(professional_id=professional_id).filter(
        Request.status.in_(["pending", "in progress"])
    ).count()
    pending_requests = Request.query.filter_by(status="requested").count()

    # Compute total earnings
    total_earnings = db.session.query(db.func.sum(Service.price)).join(Request).filter(
        Request.professional_id == professional_id,
        Request.status == "closed"
    ).scalar() or 0.0

    # Retrieve feedbacks
    feedbacks = Feedback.query.filter_by(professional_id=professional_id).all()

    # Calculate average rating
    average_rating = round(sum([f.rating for f in feedbacks]) / len(feedbacks), 1) if feedbacks else 0

    # Monthly Service Breakdown
    monthly_service_breakdown = {
        month: Request.query.filter_by(professional_id=professional_id).filter(
            extract("month", Request.request_date) == idx + 1
        ).count()
        for idx, month in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
    }
    monthly_services_chart = generate_chart(monthly_service_breakdown, "bar", "Monthly Services", "monthly_services.png")

    # Rating Distribution
    rating_distribution = {
        star: Feedback.query.filter_by(professional_id=professional_id, rating=star).count()
        for star in range(1, 6)
    }
    rating_distribution_chart = generate_chart(rating_distribution, "pie", "Rating Distribution", "rating_distribution.png")

    # Customer Feedback
    customer_feedback = Feedback.query.filter_by(professional_id=professional_id).all()

    return render_template(
        "professional/professional_summary.html",
        professional=professional,
        completed_services=completed_services,
        accepted_services=accepted_services,
        pending_requests=pending_requests,
        total_earnings=total_earnings,
        average_rating=average_rating,  # Ensure this is defined
        monthly_service_breakdown=monthly_service_breakdown,
        rating_distribution=rating_distribution,
        customer_feedback=customer_feedback,
        charts={
            "monthly_services": monthly_services_chart,
            "rating_distribution": rating_distribution_chart,
        },
    )



@app.route('/professional_profile', methods=['GET', 'POST'])
def professional_profile():
    professional_id = session.get('user_id')  # Assuming the professional's ID is stored in the session
    professional = Professional.query.get(professional_id)

    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        service_type = request.form.get('service')
        experience = request.form.get('experience')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        phone_number = request.form.get('contact')

        # Update professional details
        professional.name = name
        if password:
            professional.password = password  # The setter will hash it
        professional.service_type = service_type
        professional.experience = int(experience)
        professional.address = address
        professional.pincode = pincode
        professional.phone_number = phone_number

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('professional_profile'))

    return render_template('professional/professional_profile.html', professional=professional)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    """
    Update the profile of the logged-in professional.
    """
    professional_id = session.get('user_id')  # Assuming the professional is logged in
    professional = Professional.query.get(professional_id)

    if not professional:
        flash('Professional not found!', 'danger')
        return redirect(url_for('professional_profile'))

    # Get form data
    name = request.form.get('name')
    password = request.form.get('password')
    service_type = request.form.get('service')
    experience = request.form.get('experience')
    address = request.form.get('address')
    pincode = request.form.get('pincode')
    phone_number = request.form.get('contact')

    # Update professional fields
    professional.name = name
    if password:  # Only update password if provided
        professional.password = password
    professional.service_type = service_type
    professional.experience = int(experience) if experience.isdigit() else professional.experience
    professional.address = address
    professional.pincode = pincode
    professional.phone_number = phone_number

    try:
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating the profile.', 'danger')
        print(f"Error updating profile: {e}")

    return redirect(url_for('professional_profile'))




@app.route('/accept_service/<id>', methods=['POST'])
def accept_service(id):
    professional_id = session.get('user_id')  # Assuming professional is logged in
    service_request = Request.query.get(id)

    if service_request and service_request.status == 'requested':
        service_request.status = 'pending'
        service_request.professional_id = professional_id  # Assign to the logged-in professional

        service_request.customer_status = 'accepted'
        db.session.commit()
        flash('Service request accepted successfully!', 'success')
    else:
        flash('Unable to accept the service request.', 'danger')

    return redirect(url_for('professional_dashboard'))  


     # Assuming professional is logged in
import json

@app.route('/reject_service/<id>', methods=['POST'])
def reject_service(id):
    professional_id = session.get('user_id')  # Get the logged-in professional ID
    service_request = db.session.get(Request, id)  # Fetch the service request

    if service_request and service_request.status == 'requested':
        # Initialize `rejected_by` if it's None or invalid
        try:
            if isinstance(service_request.rejected_by, str):
                service_request.rejected_by = json.loads(service_request.rejected_by)
        except json.JSONDecodeError:
            service_request.rejected_by = []  # Reset to an empty list if invalid

        # Ensure `rejected_by` is a list
        if not isinstance(service_request.rejected_by, list):
            service_request.rejected_by = []

        # Append the professional ID if not already present
        if professional_id not in service_request.rejected_by:
            service_request.rejected_by.append(professional_id)

        # Serialize back to JSON if necessary
        service_request.rejected_by = json.dumps(service_request.rejected_by)

        try:
            db.session.commit()
            flash('Service request successfully rejected.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error rejecting service request: {str(e)}', 'danger')
    else:
        flash('Unable to reject the service request.', 'danger')

    return redirect(url_for('professional_dashboard'))







@app.route('/start_service/<id>', methods=['POST'])
def start_service(id):
    professional_id = session.get('user_id')  # Assuming professional is logged in
    service_request = Request.query.get(id)
    source_page = request.args.get('source', 'professional_dashboard')

    if service_request and service_request.professional_id == professional_id and service_request.status == 'pending':
        service_request.status = 'in progress'  # Update status to "in progress"
        db.session.commit()
        flash('Service started successfully!', 'success')
    else:
        flash('Unable to start the service.', 'danger')

    return redirect(url_for(source_page))

@app.route('/close_service/<id>', methods=['POST'])
def close_service(id):
    professional_id = session.get('user_id')  # Assuming professional is logged in
    service_request = Request.query.get(id)
    source_page = request.args.get('source', 'professional_dashboard')

    if service_request and service_request.professional_id == professional_id and service_request.status == 'in progress':
        service_request.status = 'review pending'  # Update status to "review pending"
        service_request.completion_date = datetime.utcnow()  # Set completion date
        db.session.commit()
        flash('Service closed successfully! Awaiting customer review.', 'success')
    else:
        flash('Unable to close the service.', 'danger')

    return redirect(url_for(source_page))






@app.route('/customer_dashboard', methods=['GET', 'POST'])
def customer_dashboard():
    customer_id = session.get('user_id')
    customer = User.query.get(customer_id)
    
    available_services = Service.query.all()
    
    selected_service_name = request.args.get('service_name', None)
    if selected_service_name:
        best_packages = Service.query.filter_by(service_name=selected_service_name).all()
    else:
        best_packages = Service.query.all()
    
    service_history = Request.query.filter_by(customer_id=customer_id).order_by(Request.request_date.desc()).all()
    
    # Pass the request object to the template
    return render_template(
        'customer/customer_dashboard.html',
        customer=customer,
        available_services=available_services,
        best_packages=best_packages,
        service_history=service_history,
        selected_service_name=selected_service_name,
        request=request  # Add this line to pass the request object
    )
    




@app.route('/book_service/<id>', methods=['POST'])
def book_service(id):
    customer_id = session.get('user_id')  # Get the logged-in user ID
    service = Service.query.get(id)  # Retrieve the service based on the ID

    if service:
        # Retrieve the date from the form
        request_date_str = request.form.get('request_date')
        try:
            request_date = datetime.strptime(request_date_str, '%Y-%m-%d')  # Convert to a datetime object
        except ValueError:
            flash('Invalid date format. Please select a valid date.', 'danger')
            return redirect(request.referrer or url_for('customer_dashboard'))  # Redirect to the referring page

        # Create a new service request
        new_request = Request(
            customer_id=customer_id,
            service_id=service.id,
            status='requested',
            request_date=request_date
        )
        try:
            db.session.add(new_request)
            db.session.commit()
            flash('Service booked successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to book the service: {str(e)}', 'danger')
    else:
        flash('Service not found.', 'danger')

    # Redirect back to the referring page or default to the customer dashboard
    return redirect(request.referrer or url_for('customer_dashboard'))




@app.route('/cancel_service/<id>', methods=['POST'])
def cancel_service(id):
    customer_id = session.get('user_id')
    service_request = Request.query.get(id)
    
    if service_request and service_request.customer_id == customer_id and service_request.status in ['requested', 'pending']:
        service_request.status = 'canceled'  # Update the status to 'canceled'
        db.session.commit()
        flash('Service request canceled successfully!', 'success')
    else:
        flash('Unable to cancel the service request.', 'danger')
    
    return redirect(url_for('customer_dashboard'))



@app.route('/add_review/<id>', methods=['POST'])
def add_review(id):
    customer_id = session.get('user_id')
    service_request = Request.query.get(id)
    review = request.form.get('review')
    rating = request.form.get('rating')

    # Debugging prints
    print(f"Service Request: {service_request}")
    print(f"Customer ID from session: {customer_id}")
    print(f"Service Request Status: {service_request.status if service_request else 'N/A'}")
    service_request = Request.query.get(id)
    if rating is None:
        flash('Please select a rating.', 'danger')
        return redirect(url_for('customer_dashboard'))
    
    try:
        rating = int(rating)
    except ValueError:
        flash('Invalid rating value.', 'danger')
        return redirect(url_for('customer_dashboard'))
        flash('Invalid rating value.', 'danger')
    if service_request and service_request.customer_id == customer_id and service_request.status == 'review pending':
        service_request.status = 'closed'
        new_feedback = Feedback(
            request_id=service_request.id,
            customer_id=customer_id,
            professional_id=service_request.professional_id,
            rating=rating,
            comments=review,
            feedback_date=datetime.utcnow()
        )
        service_request.status = 'closed'
        db.session.add(new_feedback)
        db.session.commit()
        flash('Review submitted successfully!', 'success')
    else:
        flash('Unable to submit the review.', 'danger')
        flash('Unable to submit the review.', 'danger')
    return redirect(url_for('customer_dashboard'))






@app.route('/customer_search', methods=['GET'])
def customer_search():
    # Get the logged-in customer ID
    customer_id = session.get('user_id')
    customer = Customer.query.get(customer_id)

    # Retrieve search query from request
    search_query = request.args.get('search_query', '')

    # Query services based on the search input
    query = Service.query
    if search_query:
        query = query.filter(Service.service_name.contains(search_query) | Service.service_description.contains(search_query))

    filtered_services = query.all()

    return render_template(
        'customer/customer_search.html',
        customer=customer,
        search_query=search_query,
        filtered_services=filtered_services
    )

@app.route("/customer_summary")
def customer_summary():
    customer_id = session.get("user_id")  # Assuming customer's ID is stored in session
    customer = Customer.query.get(customer_id)

    # Total Services Taken
    total_services_taken = Request.query.filter_by(customer_id=customer_id).count()

    # Service Requests by Type
    services = Service.query.all()
    service_requests = {
        service.service_name: Request.query.filter_by(customer_id=customer_id, service_id=service.id).count()
        for service in services
    }
    service_requests_chart = generate_chart(
        service_requests, "bar", "Service Requests Chart", "service_requests_chart.png"
    )

    return render_template(
        "customer/customer_summary.html",
        customer=customer,
        total_services_taken=total_services_taken,
        service_requests=service_requests,
        charts={"service_requests": service_requests_chart},
    )

@app.route('/customer_profile', methods=['GET', 'POST'])
def customer_profile():
    customer_id = session.get('user_id')  # Assuming the customer ID is stored in the session
    customer = Customer.query.get(customer_id)

    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        phone_number = request.form.get('contact')

        # Update customer details
        customer.name = name
        if password:
            customer.password = password  # Assuming the password setter hashes it
        customer.address = address
        customer.pincode = pincode
        customer.phone_number = phone_number

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('customer_profile'))

    return render_template('customer/customer_profile.html', customer=customer)


@app.route('/update_customer_profile', methods=['POST'])
def update_customer_profile():
    customer_id = session.get('user_id')  # Assuming the customer is logged in
    customer = Customer.query.get(customer_id)

    if not customer:
        flash('Customer not found!', 'danger')
        return redirect(url_for('customer_profile'))

    # Get form data
    name = request.form.get('name')
    password = request.form.get('password')
    address = request.form.get('address')
    pincode = request.form.get('pincode')
    phone_number = request.form.get('contact')

    # Update customer fields
    customer.name = name
    if password:  # Only update password if provided
        customer.password = password
    customer.address = address
    customer.pincode = pincode
    customer.phone_number = phone_number

    try:
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating the profile.', 'danger')
        print(f"Error updating profile: {e}")

    return redirect(url_for('customer_profile'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True)