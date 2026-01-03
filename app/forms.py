from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, RadioField
from wtforms.fields import TimeField  # Correct import for TimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password')])

class DriverRegistrationForm(FlaskForm):
    # Account fields
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    
    # Driver info
    license_number = StringField('License Number', validators=[DataRequired()])
    vehicle_type = SelectField('Vehicle Type', 
                              choices=[
                                  ('', 'Select Vehicle Type'),
                                  ('car', 'Car'),
                                  ('motorcycle', 'Motorcycle'),
                                  ('scooter', 'Scooter'),
                                  ('bicycle', 'Bicycle'),
                                  ('van', 'Van'),
                                  ('truck', 'Truck')
                              ],
                              validators=[DataRequired()])
    vehicle_model = StringField('Vehicle Model', validators=[Optional()])
    license_plate = StringField('License Plate', validators=[Optional()])
    
    # Emergency contact
    emergency_contact = StringField('Emergency Contact', validators=[Optional()])
    emergency_phone = StringField('Emergency Phone', validators=[Optional()])
    
    # Shift information
    shift_start = TimeField('Shift Start Time', validators=[Optional()], format='%H:%M')
    shift_end = TimeField('Shift End Time', validators=[Optional()], format='%H:%M')
    
    # Status fields
    is_available = BooleanField('Available for deliveries', default=True)
    is_on_shift = BooleanField('Currently on shift', default=False)

class DriverEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    password = PasswordField('New Password (leave blank to keep current)', 
                            validators=[Optional(), Length(min=8)])
    
    # Driver info
    license_number = StringField('License Number', validators=[DataRequired()])
    vehicle_type = SelectField('Vehicle Type', 
                              choices=[
                                  ('', 'Select Vehicle Type'),
                                  ('car', 'Car'),
                                  ('motorcycle', 'Motorcycle'),
                                  ('scooter', 'Scooter'),
                                  ('bicycle', 'Bicycle'),
                                  ('van', 'Van'),
                                  ('truck', 'Truck')
                              ],
                              validators=[DataRequired()])
    vehicle_model = StringField('Vehicle Model', validators=[Optional()])
    license_plate = StringField('License Plate', validators=[Optional()])
    
    # Emergency contact
    emergency_contact = StringField('Emergency Contact', validators=[Optional()])
    emergency_phone = StringField('Emergency Phone', validators=[Optional()])
    
    # Shift information
    shift_start = TimeField('Shift Start Time', validators=[Optional()], format='%H:%M')
    shift_end = TimeField('Shift End Time', validators=[Optional()], format='%H:%M')
    
    # Status fields
    is_available = BooleanField('Available', default=True)
    is_on_shift = BooleanField('On Shift', default=False)
    
    # User status
    status = RadioField('Status', 
                       choices=[('active', 'Active'), ('inactive', 'Inactive')],
                       validators=[DataRequired()],
                       default='active')