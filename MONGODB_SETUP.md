# MongoDB Setup Guide for News Bot

## Setting up MongoDB for News Bot

### 1. Install MongoDB (if not already installed)

For Windows:
- Download MongoDB Community Server from https://www.mongodb.com/try/download/community
- Follow the installation wizard
- During installation, you can choose to install MongoDB as a Windows service

### 2. Start MongoDB Server

If installed as a service, MongoDB will start automatically. Otherwise, start it manually:

```bash
# If using MongoDB Server service
# The service should start automatically

# If running MongoDB manually
"C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe"
```

### 3. Install MongoDB Compass (GUI Interface)

- Download MongoDB Compass from https://www.mongodb.com/products/compass
- Install and run MongoDB Compass
- Connect to your local MongoDB instance (usually localhost:27017)

### 4. Configure the News Bot

The news bot is already configured to work with MongoDB. Check the config.py file:

```python
MONGO_URI = 'mongodb://localhost:27017'
DATABASE_NAME = 'news_sitemap'
COLLECTION_NAME = 'articles'
```

### 5. Verify MongoDB Connection

Run the following command to test your MongoDB connection:

```python
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
# Test the connection
client.admin.command('ping')
print("MongoDB connection successful!")
```

### 6. Using MongoDB Compass

1. Open MongoDB Compass
2. Connect to `mongodb://localhost:27017`
3. You should see the `news_sitemap` database after running the crawler
4. The `articles` collection will contain all crawled news items
5. You can view, search, filter, and analyze your data using Compass

### 7. Troubleshooting

**If MongoDB is not starting:**
- Check if the MongoDB service is running in Windows Services
- Ensure the data directory exists (usually `C:\data\db`)
- Check the log file for errors

**If the connection fails:**
- Verify MongoDB is running
- Check firewall settings
- Verify the connection string in config.py

**To manually create the data directory (if needed):**
```bash
mkdir C:\data\db
```

### 8. Sample Queries in MongoDB Compass

Once you have data in your collection, you can run queries like:

- Find all articles from a specific domain:
  ```javascript
  { "loc": { $regex: "aajtak.in" } }
  ```

- Find all articles with titles:
  ```javascript
  { "title": { $exists: true, $ne: "" } }
  ```

- Find articles from a specific date:
  ```javascript
  { "publication_date": { $regex: "^2023" } }
  ```

- Find all articles from HTML crawling:
  ```javascript
  { "source_type": "html_content" }
  ```

### 9. Running the Enhanced Crawler

To run the enhanced crawler with MongoDB integration:

```bash
cd test4
python enhanced_main.py
```

The crawler will now:
1. Extract news from sitemaps (if available)
2. Crawl HTML content directly from websites
3. Use custom selectors for specific sites (like aajtak.in, indiatv.in)
4. Store all data in MongoDB
5. Update the database with new entries