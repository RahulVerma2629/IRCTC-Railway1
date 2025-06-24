import os
import logging
from datetime import datetime, timedelta
import random
import string
from flask import render_template, redirect, url_for, flash, request, abort, jsonify, send_file
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User, Station, Train, TrainSchedule, Seat, Booking, BookingDetail
from forms import (RegistrationForm, LoginForm, AdminLoginForm, UpdateProfileForm, SearchTrainForm,
                  PassengerForm, BookingForm, TrainForm, ScheduleForm)
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def init_routes(app):
    
    # Helper functions
    def generate_booking_number(length=8):
        """Generate a random booking number"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    def generate_seat_numbers(total_seats):
        """Generate seat numbers based on total seats"""
        seats = []
        # Create seats in format: Row (A-Z) + Number (1-6)
        rows = min(total_seats // 6 + (1 if total_seats % 6 else 0), 26)  # Max 26 rows (A-Z)
        for r in range(rows):
            row_letter = chr(65 + r)  # A=65, B=66, etc.
            for n in range(1, 7):  # 6 seats per row
                if len(seats) < total_seats:
                    seats.append(f"{row_letter}{n}")
        return seats
    
    def create_seats_for_schedule(schedule, total_seats):
        """Create seat records for a train schedule"""
        seat_numbers = generate_seat_numbers(total_seats)
        for seat_number in seat_numbers:
            seat = Seat(schedule_id=schedule.id, seat_number=seat_number, is_booked=False)
            db.session.add(seat)
        db.session.commit()
    
    def create_train_schedule(train_id, date):
        """Create a new train schedule"""
        train = Train.query.get(train_id)
        if not train:
            return None
            
        # Check if schedule already exists
        existing_schedule = TrainSchedule.query.filter_by(train_id=train_id, date=date).first()
        if existing_schedule:
            return existing_schedule
            
        # Create new schedule
        schedule = TrainSchedule(
            train_id=train_id,
            date=date,
            available_seats=train.total_seats
        )
        db.session.add(schedule)
        db.session.commit()
        
        # Create seats for this schedule
        create_seats_for_schedule(schedule, train.total_seats)
        
        return schedule
    
    def generate_ticket_pdf(booking):
        """Generate a PDF ticket for a booking"""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Add a header
        p.setFont("Helvetica-Bold", 18)
        p.drawString(30, height - 40, "Railway Booking System")
        p.setFont("Helvetica", 12)
        p.drawString(30, height - 60, "E-Ticket")
        
        # Add a horizontal line
        p.line(30, height - 70, width - 30, height - 70)
        
        # Booking details
        p.setFont("Helvetica-Bold", 14)
        p.drawString(30, height - 100, f"Booking #: {booking.booking_number}")
        
        # Get train and schedule details
        schedule = TrainSchedule.query.get(booking.schedule_id)
        train = Train.query.get(schedule.train_id)
        origin = Station.query.get(train.origin_id)
        destination = Station.query.get(train.destination_id)
        
        # Train info
        p.setFont("Helvetica-Bold", 12)
        p.drawString(30, height - 130, "Train Information:")
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 150, f"Train: {train.name} ({train.number})")
        p.drawString(50, height - 170, f"From: {origin.name} ({origin.code})")
        p.drawString(50, height - 190, f"To: {destination.name} ({destination.code})")
        p.drawString(50, height - 210, f"Date: {schedule.date.strftime('%B %d, %Y')}")
        p.drawString(50, height - 230, f"Departure: {train.departure_time.strftime('%H:%M')}")
        p.drawString(50, height - 250, f"Arrival: {train.arrival_time.strftime('%H:%M')}")
        
        # Passenger information
        p.setFont("Helvetica-Bold", 12)
        p.drawString(30, height - 280, "Passenger Details:")
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 300, "Name")
        p.drawString(200, height - 300, "Age")
        p.drawString(250, height - 300, "Gender")
        p.drawString(320, height - 300, "Seat")
        
        y_position = height - 320
        for i, passenger in enumerate(booking.passengers):
            seat = Seat.query.get(passenger.seat_id)
            p.drawString(50, y_position, passenger.passenger_name)
            p.drawString(200, y_position, str(passenger.passenger_age))
            p.drawString(250, y_position, passenger.passenger_gender.capitalize())
            p.drawString(320, y_position, seat.seat_number)
            y_position -= 20
        
        # Fare details
        p.setFont("Helvetica-Bold", 12)
        p.drawString(30, y_position - 30, "Fare Details:")
        p.setFont("Helvetica", 10)
        p.drawString(50, y_position - 50, f"Total Passengers: {booking.total_passengers}")
        p.drawString(50, y_position - 70, f"Total Amount: ₹{booking.total_amount:.2f}")
        
        # Footer
        p.setFont("Helvetica-Oblique", 8)
        p.drawString(30, 30, "This is a computer-generated ticket and does not require a signature.")
        
        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer
    
    # Home route
    @app.route('/')
    def index():
        form = SearchTrainForm()
        # Populate the station dropdowns
        form.origin.choices = [(s.id, f"{s.name} ({s.code})") for s in Station.query.order_by(Station.name).all()]
        form.destination.choices = [(s.id, f"{s.name} ({s.code})") for s in Station.query.order_by(Station.name).all()]
        return render_template('index.html', form=form)
    
    # User Authentication Routes
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data)
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=hashed_password,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone_number=form.phone_number.data
            )
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html', form=form, title='Register')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Login unsuccessful. Please check email and password.', 'danger')
        
        return render_template('login.html', form=form, title='Login')
    
    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('index'))
    
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        form = UpdateProfileForm()
        
        if form.validate_on_submit():
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.phone_number = form.phone_number.data
            db.session.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('profile'))
        
        elif request.method == 'GET':
            form.first_name.data = current_user.first_name
            form.last_name.data = current_user.last_name
            form.phone_number.data = current_user.phone_number
        
        return render_template('profile.html', form=form, title='Profile')
    
    # Train Search and Booking Routes
    @app.route('/search', methods=['GET', 'POST'])
    def search():
        form = SearchTrainForm()
        # Populate the station dropdowns
        form.origin.choices = [(s.id, f"{s.name} ({s.code})") for s in Station.query.order_by(Station.name).all()]
        form.destination.choices = [(s.id, f"{s.name} ({s.code})") for s in Station.query.order_by(Station.name).all()]
        
        if form.validate_on_submit():
            origin_id = form.origin.data
            destination_id = form.destination.data
            travel_date = form.date.data
            
            return redirect(url_for('trains', origin=origin_id, destination=destination_id, date=travel_date))
        
        return render_template('search.html', form=form, title='Search Trains')
    
    @app.route('/trains')
    def trains():
        origin_id = request.args.get('origin', type=int)
        destination_id = request.args.get('destination', type=int)
        date_str = request.args.get('date')
        
        if not all([origin_id, destination_id, date_str]):
            flash('Invalid search parameters.', 'danger')
            return redirect(url_for('search'))
        
        try:
            travel_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('search'))
        
        # Get origin and destination stations
        origin = Station.query.get_or_404(origin_id)
        destination = Station.query.get_or_404(destination_id)
        
        # Try to fetch trains from IRCTC API first
        from irctc_api import search_trains, map_irctc_train_to_db_format, check_api_credentials
        
        available_trains = []
        
        # Check if API credentials are available
        if check_api_credentials():
            try:
                # Try to get trains from IRCTC API
                irctc_trains = search_trains(origin.code, destination.code, date_str)
                
                if irctc_trains:
                    # Process API results
                    for irctc_train in irctc_trains:
                        # Map IRCTC train to our format
                        train_data = map_irctc_train_to_db_format(irctc_train, origin.code, destination.code)
                        
                        # Check if this train already exists in our database
                        train = Train.query.filter_by(number=train_data['number']).first()
                        
                        if not train:
                            # Create a new train if it doesn't exist
                            train = Train(
                                name=train_data['name'],
                                number=train_data['number'],
                                origin_id=origin_id,
                                destination_id=destination_id,
                                departure_time=train_data['departure_time'],
                                arrival_time=train_data['arrival_time'],
                                total_seats=train_data['total_seats'],
                                price=train_data['price']
                            )
                            db.session.add(train)
                            db.session.commit()
                        
                        # Check for schedule
                        schedule = TrainSchedule.query.filter_by(train_id=train.id, date=travel_date).first()
                        if not schedule:
                            schedule = create_train_schedule(train.id, travel_date)
                        
                        if schedule and schedule.available_seats > 0:
                            available_trains.append({
                                'train': train,
                                'schedule': schedule,
                                'available_seats': schedule.available_seats
                            })
            except Exception as e:
                app.logger.error(f"Error fetching trains from IRCTC API: {str(e)}")
                # If API fails, we'll fall back to local data
        
        # If no trains from API or API failed, use local database as fallback
        if not available_trains:
            app.logger.info("Using local database for train search")
            # Find trains between these stations in our database
            trains = Train.query.filter_by(origin_id=origin_id, destination_id=destination_id).all()
            
            # For each train, create or get schedule for the selected date
            for train in trains:
                # Check if schedule exists
                schedule = TrainSchedule.query.filter_by(train_id=train.id, date=travel_date).first()
                
                # If not, create one
                if not schedule:
                    schedule = create_train_schedule(train.id, travel_date)
                
                if schedule and schedule.available_seats > 0:
                    available_trains.append({
                        'train': train,
                        'schedule': schedule,
                        'available_seats': schedule.available_seats
                    })
        
        return render_template(
            'trains.html', 
            trains=available_trains, 
            origin=origin, 
            destination=destination, 
            date=travel_date,
            title='Available Trains'
        )
    
    @app.route('/select-seat/<int:schedule_id>')
    @login_required
    def select_seat(schedule_id):
        schedule = TrainSchedule.query.get_or_404(schedule_id)
        train = Train.query.get_or_404(schedule.train_id)
        
        # Get all seats for this schedule
        seats = Seat.query.filter_by(schedule_id=schedule_id).order_by(Seat.seat_number).all()
        
        # Organize seats by row for UI
        seat_map = {}
        for seat in seats:
            row = seat.seat_number[0]  # Get the row letter
            if row not in seat_map:
                seat_map[row] = []
            seat_map[row].append(seat)
        
        return render_template(
            'select_seat.html',
            schedule=schedule,
            train=train,
            seat_map=seat_map,
            title='Select Seats'
        )
    
    @app.route('/booking-summary', methods=['POST'])
    @login_required
    def booking_summary():
        # Get selected seats
        selected_seats_str = request.form.get('selected_seats', '')
        selected_seats = selected_seats_str.split(',') if selected_seats_str else []
        schedule_id = request.form.get('schedule_id')
        
        if not selected_seats or not schedule_id:
            flash('Please select at least one seat.', 'danger')
            return redirect(url_for('select_seat', schedule_id=schedule_id))
        
        schedule = TrainSchedule.query.get_or_404(schedule_id)
        train = Train.query.get_or_404(schedule.train_id)
        origin = Station.query.get_or_404(train.origin_id)
        destination = Station.query.get_or_404(train.destination_id)
        
        # Get the selected seat objects
        seats = Seat.query.filter(Seat.id.in_(selected_seats), Seat.schedule_id==schedule_id).all()
        
        # Prepare passenger forms
        passenger_forms = []
        for _ in range(len(seats)):
            form = PassengerForm()
            passenger_forms.append(form)
        
        # Calculate total amount
        total_amount = len(seats) * train.price
        
        return render_template(
            'booking_summary.html',
            schedule=schedule,
            train=train,
            origin=origin,
            destination=destination,
            seats=seats,
            passenger_forms=passenger_forms,
            total_amount=total_amount,
            title='Booking Summary'
        )
    
    @app.route('/confirm-booking', methods=['POST'])
    @login_required
    def confirm_booking():
        schedule_id = request.form.get('schedule_id')
        seat_ids = request.form.getlist('seat_id[]')
        passenger_names = request.form.getlist('passenger_name')
        passenger_ages = request.form.getlist('passenger_age')
        passenger_genders = request.form.getlist('passenger_gender')
        
        # Log the form data for debugging
        app.logger.debug(f"Schedule ID: {schedule_id}")
        app.logger.debug(f"Seat IDs: {seat_ids}")
        app.logger.debug(f"Passenger Names: {passenger_names}")
        app.logger.debug(f"Passenger Ages: {passenger_ages}")
        app.logger.debug(f"Passenger Genders: {passenger_genders}")
        
        if not all([schedule_id, seat_ids, passenger_names, passenger_ages, passenger_genders]):
            missing = []
            if not schedule_id: missing.append("schedule_id")
            if not seat_ids: missing.append("seat_ids")
            if not passenger_names: missing.append("passenger_names")
            if not passenger_ages: missing.append("passenger_ages")
            if not passenger_genders: missing.append("passenger_genders")
            flash(f'Invalid booking data. Missing: {", ".join(missing)}', 'danger')
            return redirect(url_for('index'))
        
        schedule = TrainSchedule.query.get_or_404(schedule_id)
        train = Train.query.get_or_404(schedule.train_id)
        origin = Station.query.get_or_404(train.origin_id)
        destination = Station.query.get_or_404(train.destination_id)
        
        # Validate seat availability
        seats = Seat.query.filter(Seat.id.in_(seat_ids)).all()
        if any(seat.is_booked for seat in seats):
            flash('Some selected seats are no longer available.', 'danger')
            return redirect(url_for('select_seat', schedule_id=schedule_id))
        
        # Calculate total amount
        total_amount = len(seats) * train.price
        
        # Store form data in session for payment
        form_data = {
            'schedule_id': schedule_id,
            'passenger_name': passenger_names,
            'passenger_age': passenger_ages,
            'passenger_gender': passenger_genders,
            'seat_id[]': seat_ids
        }
        
        # Render payment page
        return render_template(
            'payment.html',
            schedule=schedule,
            train=train,
            origin=origin,
            destination=destination,
            seats=seats,
            total_amount=total_amount,
            form_data=form_data,
            title='Payment'
        )
        
    @app.route('/process-payment', methods=['POST'])
    @login_required
    def process_payment():
        # Get form data
        schedule_id = request.form.get('schedule_id')
        seat_ids = request.form.getlist('seat_id[]')
        passenger_names = request.form.getlist('passenger_name')
        passenger_ages = request.form.getlist('passenger_age')
        passenger_genders = request.form.getlist('passenger_gender')
        
        # Payment details (just for demonstration)
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        cvv = request.form.get('cvv')
        name_on_card = request.form.get('name_on_card')
        
        # Log form data for debugging
        app.logger.debug(f"Process Payment Data:")
        app.logger.debug(f"Schedule ID: {schedule_id}")
        app.logger.debug(f"Seat IDs: {seat_ids}")
        app.logger.debug(f"Passenger Names: {passenger_names}")
        app.logger.debug(f"Passenger Ages: {passenger_ages}")
        app.logger.debug(f"Passenger Genders: {passenger_genders}")
        
        # Validate form data
        if not all([schedule_id, seat_ids, passenger_names, passenger_ages, passenger_genders, 
                   card_number, expiry_date, cvv, name_on_card]):
            flash('Please fill out all payment details.', 'danger')
            return redirect(url_for('index'))
        
        # Convert data if it came in as a string representation of a list
        if isinstance(seat_ids, str) and seat_ids.startswith('['):
            seat_ids = eval(seat_ids)
        if isinstance(passenger_names[0], str) and passenger_names[0].startswith('['):
            passenger_names = eval(passenger_names[0])
        if isinstance(passenger_ages[0], str) and passenger_ages[0].startswith('['):
            passenger_ages = [int(age.strip("'[]")) for age in passenger_ages[0].split(',')]
        if isinstance(passenger_genders[0], str) and passenger_genders[0].startswith('['):
            passenger_genders = eval(passenger_genders[0])
        
        # Ensure seat_ids is a list
        if not isinstance(seat_ids, list):
            seat_ids = [seat_ids]
        
        schedule = TrainSchedule.query.get_or_404(schedule_id)
        train = Train.query.get_or_404(schedule.train_id)
        
        # Validate seat availability again
        seats = Seat.query.filter(Seat.id.in_(seat_ids)).all()
        if any(seat.is_booked for seat in seats):
            flash('Some selected seats are no longer available.', 'danger')
            return redirect(url_for('select_seat', schedule_id=schedule_id))
        
        # Generate booking number
        booking_number = generate_booking_number()
        
        # Calculate total amount
        total_amount = len(seats) * train.price
        
        try:
            # Create booking
            booking = Booking(
                user_id=current_user.id,
                schedule_id=schedule_id,
                booking_number=booking_number,
                total_passengers=len(seats),
                total_amount=total_amount,
                status='confirmed'
            )
            db.session.add(booking)
            db.session.flush()  # Get booking ID before committing
            
            # Create booking details and mark seats as booked
            for i, seat_id in enumerate(seat_ids):
                # Convert passenger age to integer if it's a string
                passenger_age = passenger_ages[i]
                if isinstance(passenger_age, str):
                    passenger_age = int(passenger_age)
                
                # Get passenger name and gender
                passenger_name = passenger_names[i]
                passenger_gender = passenger_genders[i]
                
                app.logger.debug(f"Creating booking detail: seat_id={seat_id}, name={passenger_name}, age={passenger_age}, gender={passenger_gender}")
                
                # Create booking detail
                booking_detail = BookingDetail(
                    booking_id=booking.id,
                    seat_id=seat_id,
                    passenger_name=passenger_name,
                    passenger_age=passenger_age,
                    passenger_gender=passenger_gender
                )
                db.session.add(booking_detail)
                
                # Mark seat as booked
                seat = Seat.query.get(seat_id)
                seat.is_booked = True
            
            # Update available seats count
            schedule.available_seats -= len(seats)
            
            db.session.commit()
            
            flash('Payment successful! Booking confirmed.', 'success')
            return redirect(url_for('confirmation', booking_id=booking.id))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error processing payment: {str(e)}")
            flash(f'Error processing payment: {str(e)}', 'danger')
            return redirect(url_for('index'))
    
    @app.route('/confirmation/<int:booking_id>')
    @login_required
    def confirmation(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        
        # Ensure user can only view their own bookings
        if booking.user_id != current_user.id and not current_user.is_admin:
            abort(403)
        
        schedule = TrainSchedule.query.get(booking.schedule_id)
        train = Train.query.get(schedule.train_id)
        origin = Station.query.get(train.origin_id)
        destination = Station.query.get(train.destination_id)
        
        # Get booking details with seats
        booking_details = []
        for detail in booking.passengers:
            seat = Seat.query.get(detail.seat_id)
            booking_details.append({
                'detail': detail,
                'seat': seat
            })
        
        return render_template(
            'confirmation.html',
            booking=booking,
            schedule=schedule,
            train=train,
            origin=origin,
            destination=destination,
            booking_details=booking_details,
            title='Booking Confirmation'
        )
    
    @app.route('/bookings')
    @login_required
    def bookings():
        user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
        
        bookings_data = []
        for booking in user_bookings:
            schedule = TrainSchedule.query.get(booking.schedule_id)
            train = Train.query.get(schedule.train_id)
            origin = Station.query.get(train.origin_id)
            destination = Station.query.get(train.destination_id)
            
            bookings_data.append({
                'booking': booking,
                'schedule': schedule,
                'train': train,
                'origin': origin,
                'destination': destination
            })
        
        return render_template('bookings.html', bookings=bookings_data, title='My Bookings')
    
    @app.route('/ticket/<int:booking_id>')
    @login_required
    def ticket(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        
        # Ensure user can only view their own tickets
        if booking.user_id != current_user.id and not current_user.is_admin:
            abort(403)
        
        schedule = TrainSchedule.query.get(booking.schedule_id)
        train = Train.query.get(schedule.train_id)
        origin = Station.query.get(train.origin_id)
        destination = Station.query.get(train.destination_id)
        
        # Get booking details with seats
        booking_details = []
        for detail in booking.passengers:
            seat = Seat.query.get(detail.seat_id)
            booking_details.append({
                'detail': detail,
                'seat': seat
            })
        
        return render_template(
            'ticket.html',
            booking=booking,
            schedule=schedule,
            train=train,
            origin=origin,
            destination=destination,
            booking_details=booking_details,
            title='E-Ticket'
        )
    
    @app.route('/download-ticket/<int:booking_id>')
    @login_required
    def download_ticket(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        
        # Ensure user can only download their own tickets
        if booking.user_id != current_user.id and not current_user.is_admin:
            abort(403)
        
        buffer = generate_ticket_pdf(booking)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"ticket_{booking.booking_number}.pdf",
            mimetype='application/pdf'
        )
    
    @app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
    @login_required
    def cancel_booking(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        
        # Ensure user can only cancel their own bookings
        if booking.user_id != current_user.id and not current_user.is_admin:
            abort(403)
        
        # Check if booking can be cancelled (e.g., not already cancelled or completed)
        if booking.status != 'confirmed':
            flash('This booking cannot be cancelled.', 'danger')
            return redirect(url_for('bookings'))
        
        # Update booking status
        booking.status = 'cancelled'
        
        # Free up seats
        for passenger in booking.passengers:
            seat = Seat.query.get(passenger.seat_id)
            seat.is_booked = False
        
        # Update available seats in schedule
        schedule = TrainSchedule.query.get(booking.schedule_id)
        schedule.available_seats += booking.total_passengers
        
        db.session.commit()
        
        flash('Booking cancelled successfully.', 'success')
        return redirect(url_for('bookings'))
    
    # Admin Routes
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if current_user.is_authenticated and current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        
        form = AdminLoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            
            if user and check_password_hash(user.password_hash, form.password.data) and user.is_admin:
                login_user(user)
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Login unsuccessful. Please check email and password or admin status.', 'danger')
        
        return render_template('admin/login.html', form=form, title='Admin Login')
    
    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        if not current_user.is_admin:
            abort(403)
        
        # Get some stats for the dashboard
        total_users = User.query.count()
        total_trains = Train.query.count()
        total_bookings = Booking.query.count()
        total_stations = Station.query.count()
        
        # Get recent bookings
        recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
        
        booking_data = []
        for booking in recent_bookings:
            user = User.query.get(booking.user_id)
            schedule = TrainSchedule.query.get(booking.schedule_id)
            train = Train.query.get(schedule.train_id)
            
            booking_data.append({
                'booking': booking,
                'user': user,
                'train': train,
                'date': schedule.date
            })
        
        return render_template(
            'admin/dashboard.html',
            total_users=total_users,
            total_trains=total_trains,
            total_bookings=total_bookings,
            total_stations=total_stations,
            bookings=booking_data,
            title='Admin Dashboard'
        )
    
    @app.route('/admin/trains')
    @login_required
    def admin_trains():
        if not current_user.is_admin:
            abort(403)
        
        trains = Train.query.all()
        train_data = []
        
        for train in trains:
            origin = Station.query.get(train.origin_id)
            destination = Station.query.get(train.destination_id)
            
            train_data.append({
                'train': train,
                'origin': origin,
                'destination': destination
            })
        
        return render_template('admin/trains.html', trains=train_data, title='Manage Trains')
    
    @app.route('/admin/add-train', methods=['GET', 'POST'])
    @login_required
    def admin_add_train():
        if not current_user.is_admin:
            abort(403)
        
        form = TrainForm()
        # Populate station choices
        form.origin_id.choices = [(s.id, f"{s.name} ({s.code})") for s in Station.query.order_by(Station.name).all()]
        form.destination_id.choices = [(s.id, f"{s.name} ({s.code})") for s in Station.query.order_by(Station.name).all()]
        
        if form.validate_on_submit():
            train = Train(
                name=form.name.data,
                number=form.number.data,
                origin_id=form.origin_id.data,
                destination_id=form.destination_id.data,
                departure_time=form.departure_time.data,
                arrival_time=form.arrival_time.data,
                total_seats=form.total_seats.data,
                price=form.price.data
            )
            
            db.session.add(train)
            db.session.commit()
            
            flash('Train added successfully!', 'success')
            return redirect(url_for('admin_trains'))
        
        return render_template('admin/add_train.html', form=form, title='Add Train')
    
    @app.route('/admin/edit-train/<int:train_id>', methods=['GET', 'POST'])
    @login_required
    def admin_edit_train(train_id):
        if not current_user.is_admin:
            abort(403)
        
        train = Train.query.get_or_404(train_id)
        form = TrainForm()
        
        # Populate station choices
        form.origin_id.choices = [(s.id, f"{s.name} ({s.code})") for s in Station.query.order_by(Station.name).all()]
        form.destination_id.choices = [(s.id, f"{s.name} ({s.code})") for s in Station.query.order_by(Station.name).all()]
        
        if form.validate_on_submit():
            train.name = form.name.data
            train.number = form.number.data
            train.origin_id = form.origin_id.data
            train.destination_id = form.destination_id.data
            train.departure_time = form.departure_time.data
            train.arrival_time = form.arrival_time.data
            train.total_seats = form.total_seats.data
            train.price = form.price.data
            
            db.session.commit()
            
            flash('Train updated successfully!', 'success')
            return redirect(url_for('admin_trains'))
        
        elif request.method == 'GET':
            form.name.data = train.name
            form.number.data = train.number
            form.origin_id.data = train.origin_id
            form.destination_id.data = train.destination_id
            form.departure_time.data = train.departure_time
            form.arrival_time.data = train.arrival_time
            form.total_seats.data = train.total_seats
            form.price.data = train.price
        
        return render_template('admin/edit_train.html', form=form, train=train, title='Edit Train')
    
    @app.route('/admin/delete-train/<int:train_id>', methods=['POST'])
    @login_required
    def admin_delete_train(train_id):
        if not current_user.is_admin:
            abort(403)
        
        train = Train.query.get_or_404(train_id)
        
        # Check if train has any schedules with bookings
        schedules = TrainSchedule.query.filter_by(train_id=train_id).all()
        has_bookings = False
        
        for schedule in schedules:
            if Booking.query.filter_by(schedule_id=schedule.id).first():
                has_bookings = True
                break
        
        if has_bookings:
            flash('Cannot delete train with existing bookings.', 'danger')
            return redirect(url_for('admin_trains'))
        
        # Delete schedules and seats first (cascading)
        for schedule in schedules:
            Seat.query.filter_by(schedule_id=schedule.id).delete()
        
        TrainSchedule.query.filter_by(train_id=train_id).delete()
        db.session.delete(train)
        db.session.commit()
        
        flash('Train deleted successfully!', 'success')
        return redirect(url_for('admin_trains'))
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
