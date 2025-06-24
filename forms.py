from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateField, IntegerField, FloatField, TimeField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from models import User, Station, Train
from datetime import date

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class AdminLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class UpdateProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    submit = SubmitField('Update Profile')


class SearchTrainForm(FlaskForm):
    origin = SelectField('From', validators=[DataRequired()], coerce=int)
    destination = SelectField('To', validators=[DataRequired()], coerce=int)
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Search Trains')
    
    def validate_date(self, date_field):
        today = date.today()
        if date_field.data < today:
            raise ValidationError('Date cannot be in the past.')
    
    def validate(self, **kwargs):
        if not super().validate():
            return False
        if self.origin.data == self.destination.data:
            self.destination.errors = ['Origin and destination cannot be the same.']
            return False
        return True


class PassengerForm(FlaskForm):
    passenger_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    passenger_age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=1, max=120)])
    passenger_gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[DataRequired()])


class BookingForm(FlaskForm):
    schedule_id = HiddenField('Schedule ID', validators=[DataRequired()])
    total_passengers = HiddenField('Total Passengers', validators=[DataRequired()])
    total_amount = HiddenField('Total Amount', validators=[DataRequired()])
    submit = SubmitField('Confirm Booking')


class TrainForm(FlaskForm):
    name = StringField('Train Name', validators=[DataRequired(), Length(max=100)])
    number = StringField('Train Number', validators=[DataRequired(), Length(max=20)])
    origin_id = SelectField('Origin Station', validators=[DataRequired()], coerce=int)
    destination_id = SelectField('Destination Station', validators=[DataRequired()], coerce=int)
    departure_time = TimeField('Departure Time', validators=[DataRequired()], format='%H:%M')
    arrival_time = TimeField('Arrival Time', validators=[DataRequired()], format='%H:%M')
    total_seats = IntegerField('Total Seats', validators=[DataRequired(), NumberRange(min=1)])
    price = FloatField('Ticket Price', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Save Train')
    
    def validate(self, **kwargs):
        if not super().validate():
            return False
        if self.origin_id.data == self.destination_id.data:
            self.destination_id.errors = ['Origin and destination cannot be the same.']
            return False
        return True


class ScheduleForm(FlaskForm):
    train_id = SelectField('Train', validators=[DataRequired()], coerce=int)
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Add Schedule')
    
    def validate_date(self, date_field):
        today = date.today()
        if date_field.data < today:
            raise ValidationError('Date cannot be in the past.')