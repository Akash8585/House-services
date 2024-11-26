from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, Email, Length

class CustomerSignupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    pincode = StringField('Pincode', validators=[DataRequired()])
    submit = SubmitField('Register')

class ProfessionalSignupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    phone = StringField('Phone Number', validators=[DataRequired()])
    service_type = StringField('Service Type', validators=[DataRequired()])
    experience = IntegerField('Experience (Years)', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    pincode = StringField('Pincode', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AddServiceForm(FlaskForm):
    service_name = StringField('Service Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    base_price = DecimalField('Base Price', validators=[DataRequired()])
    duration = StringField('Duration', validators=[DataRequired()])
    submit = SubmitField('Add Service')