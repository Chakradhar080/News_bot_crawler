# utils.py

import logging
from datetime import datetime
import pytz
from dateutil import parser
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_duplicate(collection, loc):
    """Check if a URL already exists in the database."""
    try:
        if not loc:
            return False
        result = collection.find_one({'loc': loc})
        return result is not None
    except Exception as e:
        logger.error(f"Error checking for duplicate {loc}: {str(e)}")
        return False

def is_valid_date(publication_date):
    """Check if a publication date is valid."""
    try:
        if not publication_date:
            return False
        # Parse the publication date and make it timezone-aware
        date_obj = parser.isoparse(publication_date).astimezone(pytz.UTC)
        # Get the current time in UTC
        now = datetime.now(pytz.UTC)
        logger.debug(f"Current UTC time: {now}")
        logger.debug(f"Publication date: {date_obj}")
        # Change condition to include dates up to now
        return date_obj <= now
    except ValueError as e:
        logger.warning(f"Invalid date format: {publication_date} - {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error validating date {publication_date}: {str(e)}")
        return False

def domain_exists(collection, domain):
    """Check if articles from a domain already exist in the database."""
    try:
        if not domain:
            return False
        result = collection.find_one({'loc': {'$regex': f'{domain}'}})
        return result is not None
    except Exception as e:
        logger.error(f"Error checking domain existence for {domain}: {str(e)}")
        return False

def update_last_fetch_time():
    """Update the last fetch time in the .env file."""
    try:
        load_dotenv()  # Load environment variables from .env file

        # Get the current time in UTC
        current_time = datetime.now(pytz.UTC).isoformat()

        # Write/Override the LAST_FETCH_TIME in the .env file
        with open('.env', 'w') as f:
            f.write(f'LAST_FETCH_TIME={current_time}\n')
        logger.info(f"Updated LAST_FETCH_TIME to {current_time}")
    except Exception as e:
        logger.error(f"Error updating last fetch time: {str(e)}")
