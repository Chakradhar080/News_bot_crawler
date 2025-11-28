# config.py

import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if 'LAST_FETCH_TIME' is set in the environment variables
LAST_FETCH_TIME = os.getenv("LAST_FETCH_TIME")

if LAST_FETCH_TIME is None:
    # If 'LAST_FETCH_TIME' is not set, use the current date and time
    LAST_FETCH_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print(f"LAST_FETCH_TIME = {LAST_FETCH_TIME}")

# MongoDB connection details
MONGO_URI = 'mongodb://localhost:27017'
DATABASE_NAME = 'news_sitemap'
COLLECTION_NAME = 'articles'
