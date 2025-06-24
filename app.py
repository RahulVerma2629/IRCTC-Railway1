import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "mysql+pymysql://root:password@localhost/railway_booking")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

with app.app_context():
    # Import the models here to ensure they're created properly
    import models
    from routes import init_routes

    # Initialize routes
    init_routes(app)

    # Create database tables
    db.create_all()

    # Create admin user if not exists
    from models import User
    from werkzeug.security import generate_password_hash

    admin = User.query.filter_by(email='admin@railway.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@railway.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        logging.info('Admin user created')

    # Create some default stations if none exist
    from models import Station
    if Station.query.count() == 0:
        stations = [
            Station(name='New York', code='NYC'),
            Station(name='Boston', code='BOS'),
            Station(name='Washington DC', code='WDC'),
            Station(name='Chicago', code='CHI'),
            Station(name='Los Angeles', code='LAX'),
            Station(name='San Francisco', code='SFO'),
            Station(name='Seattle', code='SEA'),
            Station(name='Dallas', code='DAL'),
            Station(name='Miami', code='MIA'),
            Station(name='Denver', code='DEN')
        ]
        db.session.bulk_save_objects(stations)
        db.session.commit()
        logging.info('Default stations created')
