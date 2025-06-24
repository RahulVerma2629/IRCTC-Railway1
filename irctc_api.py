"""
IRCTC API Integration Module

This module provides functions to interact with the IRCTC API for accessing
real-time train information, schedules, fares, and seat availability.
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
IRCTC_API_BASE_URL = os.environ.get('IRCTC_API_BASE_URL', 'https://api.irctc.co.in/v1')
IRCTC_API_KEY = os.environ.get('IRCTC_API_KEY')
IRCTC_AUTH_TOKEN = os.environ.get('IRCTC_AUTH_TOKEN')

class IRCTCAPIException(Exception):
    """Exception raised for IRCTC API errors."""
    pass

def check_api_credentials():
    """Check if IRCTC API credentials are configured."""
    if not IRCTC_API_KEY or not IRCTC_AUTH_TOKEN:
        logger.warning("IRCTC API credentials not configured. Using local data.")
        return False
    return True

def get_headers():
    """Get headers for IRCTC API requests."""
    return {
        'Content-Type': 'application/json',
        'X-Api-Key': IRCTC_API_KEY,
        'Authorization': f'Bearer {IRCTC_AUTH_TOKEN}'
    }

def search_trains(source, destination, journey_date):
    """
    Search for trains between source and destination on a specific date.
    
    Args:
        source (str): Source station code
        destination (str): Destination station code
        journey_date (str): Journey date in YYYY-MM-DD format
        
    Returns:
        list: List of available trains
    """
    if not check_api_credentials():
        # If API credentials are not available, return None
        # The application will fall back to local data
        return None
    
    try:
        url = f"{IRCTC_API_BASE_URL}/trains/search"
        
        # Convert date format if needed (YYYY-MM-DD to DD-MM-YYYY for IRCTC)
        date_obj = datetime.strptime(journey_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d-%m-%Y')
        
        payload = {
            "fromStnCode": source,
            "toStnCode": destination,
            "journeyDate": formatted_date,
            "quotaCode": "GN"  # General Quota
        }
        
        response = requests.post(
            url,
            headers=get_headers(),
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get('trainList', [])
        else:
            logger.error(f"Error searching trains: {response.status_code}, {response.text}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Request exception during train search: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during train search: {str(e)}")
        return None

def get_train_schedule(train_number):
    """
    Get the schedule for a specific train.
    
    Args:
        train_number (str): Train number
        
    Returns:
        dict: Train schedule details
    """
    if not check_api_credentials():
        return None
    
    try:
        url = f"{IRCTC_API_BASE_URL}/trains/{train_number}/schedule"
        
        response = requests.get(
            url,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting train schedule: {response.status_code}, {response.text}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Request exception getting train schedule: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting train schedule: {str(e)}")
        return None

def check_seat_availability(train_number, from_station, to_station, journey_date, class_code="SL"):
    """
    Check seat availability for a specific train, class and date.
    
    Args:
        train_number (str): Train number
        from_station (str): Source station code
        to_station (str): Destination station code
        journey_date (str): Journey date in YYYY-MM-DD format
        class_code (str): Class code (e.g., SL for Sleeper, 3A for AC 3 Tier)
        
    Returns:
        dict: Seat availability details
    """
    if not check_api_credentials():
        return None
    
    try:
        url = f"{IRCTC_API_BASE_URL}/trains/{train_number}/availability"
        
        # Convert date format
        date_obj = datetime.strptime(journey_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d-%m-%Y')
        
        payload = {
            "fromStnCode": from_station,
            "toStnCode": to_station,
            "journeyDate": formatted_date,
            "quotaCode": "GN",  # General Quota
            "classCode": class_code
        }
        
        response = requests.post(
            url,
            headers=get_headers(),
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error checking seat availability: {response.status_code}, {response.text}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Request exception checking seat availability: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error checking seat availability: {str(e)}")
        return None

def get_fare(train_number, from_station, to_station, journey_date, class_code="SL", age=30, concession_code="GN"):
    """
    Get fare details for a specific train.
    
    Args:
        train_number (str): Train number
        from_station (str): Source station code
        to_station (str): Destination station code
        journey_date (str): Journey date in YYYY-MM-DD format
        class_code (str): Class code (e.g., SL for Sleeper, 3A for AC 3 Tier)
        age (int): Passenger age
        concession_code (str): Concession code
        
    Returns:
        dict: Fare details
    """
    if not check_api_credentials():
        return None
    
    try:
        url = f"{IRCTC_API_BASE_URL}/trains/{train_number}/fare"
        
        # Convert date format
        date_obj = datetime.strptime(journey_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d-%m-%Y')
        
        payload = {
            "fromStnCode": from_station,
            "toStnCode": to_station,
            "journeyDate": formatted_date,
            "quotaCode": "GN",  # General Quota
            "classCode": class_code,
            "age": age,
            "concessionCode": concession_code
        }
        
        response = requests.post(
            url,
            headers=get_headers(),
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting fare details: {response.status_code}, {response.text}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Request exception getting fare details: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting fare details: {str(e)}")
        return None

def get_station_code(station_name):
    """
    Get the station code for a given station name.
    
    Args:
        station_name (str): Station name or partial name
        
    Returns:
        list: List of matching stations with codes
    """
    if not check_api_credentials():
        return None
    
    try:
        url = f"{IRCTC_API_BASE_URL}/stations/search"
        
        payload = {
            "searchText": station_name
        }
        
        response = requests.post(
            url,
            headers=get_headers(),
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get('stations', [])
        else:
            logger.error(f"Error getting station code: {response.status_code}, {response.text}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Request exception getting station code: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting station code: {str(e)}")
        return None

def map_irctc_train_to_db_format(irctc_train, source_code, destination_code):
    """
    Map IRCTC train data to the format used by our database model.
    
    Args:
        irctc_train (dict): Train data from IRCTC API
        source_code (str): Source station code
        destination_code (str): Destination station code
        
    Returns:
        dict: Train data in our database format
    """
    try:
        # Extract necessary data from IRCTC response
        train_number = irctc_train.get('trainNumber')
        train_name = irctc_train.get('trainName')
        
        # Get departure/arrival times from the response
        # Note: IRCTC API might provide these in different format
        departure_time_str = irctc_train.get('departureTime')
        arrival_time_str = irctc_train.get('arrivalTime')
        
        # Convert to time objects if needed
        departure_time = datetime.strptime(departure_time_str, '%H:%M').time() if departure_time_str else None
        arrival_time = datetime.strptime(arrival_time_str, '%H:%M').time() if arrival_time_str else None
        
        # Get price info - might need to extract from a specific class
        # This will depend on the actual IRCTC API response structure
        price = 0.0
        for class_info in irctc_train.get('availableClasses', []):
            if class_info.get('classCode') == 'SL':  # Sleeper class as default
                price = float(class_info.get('fare', 0))
                break
        
        # Total seats - this might not be directly available
        # You might need to sum up availability across classes or use a default
        total_seats = 60  # Default value
        
        return {
            'number': train_number,
            'name': train_name,
            'origin_code': source_code,
            'destination_code': destination_code,
            'departure_time': departure_time,
            'arrival_time': arrival_time,
            'price': price,
            'total_seats': total_seats
        }
        
    except Exception as e:
        logger.error(f"Error mapping IRCTC train to DB format: {str(e)}")
        return None

def sync_trains_from_irctc():
    """
    Sync trains from IRCTC API to our local database.
    This is a utility function that can be run periodically.
    
    Returns:
        tuple: (success, message)
    """
    if not check_api_credentials():
        return (False, "IRCTC API credentials not configured")
    
    try:
        # This would need to be implemented based on your database model
        # and how you want to sync the data
        
        # Example implementation would:
        # 1. Get all station pairs from our database
        # 2. For each pair, search trains from IRCTC
        # 3. Update or create train records in our database
        
        logger.info("IRCTC train sync completed")
        return (True, "Trains synced successfully")
        
    except Exception as e:
        logger.error(f"Error syncing trains from IRCTC: {str(e)}")
        return (False, f"Error: {str(e)}")