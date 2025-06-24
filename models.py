from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    phone_number = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Station(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    
    # Relationships
    origin_trains = db.relationship('Train', foreign_keys='Train.origin_id', backref='origin_station', lazy=True)
    destination_trains = db.relationship('Train', foreign_keys='Train.destination_id', backref='destination_station', lazy=True)
    
    def __repr__(self):
        return f"Station('{self.name}', '{self.code}')"


class Train(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(20), unique=True, nullable=False)
    origin_id = db.Column(db.Integer, db.ForeignKey('station.id'), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey('station.id'), nullable=False)
    departure_time = db.Column(db.Time, nullable=False)
    arrival_time = db.Column(db.Time, nullable=False)
    total_seats = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    # Relationships
    schedules = db.relationship('TrainSchedule', backref='train', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"Train('{self.name}', '{self.number}')"


class TrainSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    train_id = db.Column(db.Integer, db.ForeignKey('train.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    
    # Relationships
    bookings = db.relationship('Booking', backref='schedule', lazy=True)
    seats = db.relationship('Seat', backref='schedule', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('train_id', 'date', name='_train_date_uc'),)
    
    def __repr__(self):
        return f"TrainSchedule(Train ID: {self.train_id}, Date: {self.date})"


class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('train_schedule.id'), nullable=False)
    seat_number = db.Column(db.String(10), nullable=False)
    is_booked = db.Column(db.Boolean, default=False)
    
    # Relationships
    booking_details = db.relationship('BookingDetail', backref='seat', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('schedule_id', 'seat_number', name='_schedule_seat_uc'),)
    
    def __repr__(self):
        return f"Seat('{self.seat_number}', Booked: {self.is_booked})"


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('train_schedule.id'), nullable=False)
    booking_number = db.Column(db.String(20), unique=True, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_passengers = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='confirmed')  # confirmed, cancelled, completed
    
    # Relationships
    passengers = db.relationship('BookingDetail', backref='booking', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"Booking('{self.booking_number}', Status: {self.status})"


class BookingDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False)
    passenger_name = db.Column(db.String(100), nullable=False)
    passenger_age = db.Column(db.Integer, nullable=False)
    passenger_gender = db.Column(db.String(10), nullable=False)
    
    def __repr__(self):
        return f"BookingDetail('{self.passenger_name}', Seat: {self.seat_id})"
