import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME
from utils import is_duplicate, is_valid_date, domain_exists
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_image(session, url):
    """Fetch image URL from article with timeout and error handling."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                content = await response.text()
                soup = BeautifulSoup(content, "html.parser")
                # First, try to get the OpenGraph image
                img = soup.select_one('meta[property="og:image"]')
                if img:
                    img_url = img.get("content")
                    if img_url:
                        logger.info(f"Found OpenGraph image for {url}")
                        return img_url
                
                # Fallback to the first img tag found
                img = soup.find("img")
                if img:
                    img_url = img.get("src")
                    if img_url:
                        logger.info(f"Found fallback image for {url}")
                        return img_url
                
                logger.info(f"No image found for {url}")
            else:
                logger.warning(f"HTTP {response.status} while fetching {url}")
    except asyncio.TimeoutError:
        logger.error(f"Timeout while fetching image for {url}")
    except aiohttp.ClientError as e:
        logger.error(f"Client error while fetching image for {url}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while fetching image for {url}: {str(e)}")
    return None


async def get_article_image(url):
    """Get article image with session management."""
    try:
        async with aiohttp.ClientSession() as session:
            return await fetch_image(session, url)
    except Exception as e:
        logger.error(f"Error creating session for {url}: {str(e)}")
        return None


def store_data_in_mongodb(data):
    """Store data in MongoDB with comprehensive error handling for different data types."""
    client = None
    try:
        logger.info("Connecting to MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.admin.command('ping')

        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        logger.info("Database connected successfully")

        if not data:
            logger.warning("No data to store")
            return

        # Phase 1: Collect all valid articles first (without images)
        logger.info("Filtering valid articles...")
        filtered_data = []

        for idx, item in enumerate(data):
            try:
                if not isinstance(item, dict):
                    logger.warning(f"Skipping non-dict item at index {idx}")
                    continue

                # Handle different data types - sitemap data has 'loc', HTML content has 'url'
                url_key = 'loc' if 'loc' in item else 'url'

                if url_key not in item or not item[url_key]:
                    logger.warning(f"Skipping item at index {idx} due to missing URL")
                    continue

                # Determine the source type if not already set
                if 'source_type' not in item:
                    if 'publication_name' in item and 'title' in item:
                        item['source_type'] = 'sitemap_news'
                    else:
                        item['source_type'] = 'html_content'

                # Apply filtering based on source type
                if item['source_type'].startswith('sitemap'):
                    # Handle sitemap data
                    domain = urlparse(item["loc"]).netloc
                    if not is_duplicate(collection, item["loc"]):
                        if domain_exists(collection, domain):
                            if is_valid_date(item.get("publication_date", "")):
                                filtered_data.append(item)
                        else:
                            filtered_data.append(item)
                elif item['source_type'] == 'html_content':
                    # Handle HTML content data
                    if 'url' in item and not is_duplicate(collection, item['url']):
                        filtered_data.append(item)
                else:
                    # For any other type, just check if it's a duplicate
                    url_to_check = item.get('url') or item.get('loc')
                    if url_to_check and not is_duplicate(collection, url_to_check):
                        filtered_data.append(item)

            except Exception as e:
                logger.error(f"Error processing item at index {idx}: {str(e)}")
                continue

        if not filtered_data:
            logger.info("No valid articles to process after filtering")
            return

        logger.info(f"Found {len(filtered_data)} valid articles to process")

        # Phase 2: Fetch all images for the filtered articles (only sitemap data)
        sitemap_items = [item for item in filtered_data if item.get('source_type', '').startswith('sitemap')]

        if sitemap_items:
            async def fetch_images():
                """Fetch images for sitemap articles."""
                try:
                    tasks = []
                    async with aiohttp.ClientSession() as session:
                        for item in sitemap_items:
                            if "loc" in item and item["loc"]:
                                tasks.append(asyncio.create_task(fetch_image(session, item['loc'])))

                        if tasks:
                            image_urls = await asyncio.gather(*tasks, return_exceptions=True)
                            logger.info(f"Fetched {len([u for u in image_urls if u and not isinstance(u, Exception)])} images")

                            for idx, image_url in enumerate(image_urls):
                                if image_url and not isinstance(image_url, Exception):
                                    sitemap_items[idx]["image_url"] = image_url
                        else:
                            logger.info("No image fetching tasks to execute")
                except Exception as e:
                    logger.error(f"Error in image fetching process: {str(e)}")

            # Run the image fetching process
            try:
                asyncio.run(fetch_images())
            except Exception as e:
                logger.error(f"Error running image fetching: {str(e)}")

        # Phase 3: Store articles (with or without images)
        logger.info("Storing articles in MongoDB...")
        articles_to_store = []
        for item in filtered_data:
            # Add articles regardless of whether they have images
            articles_to_store.append(item)

        if articles_to_store:
            try:
                result = collection.insert_many(articles_to_store, ordered=False)
                logger.info(f"Inserted {len(result.inserted_ids)} documents into MongoDB.")

                # Print summary of stored data types
                sitemap_count = sum(1 for item in articles_to_store if item.get('source_type', '').startswith('sitemap'))
                html_count = sum(1 for item in articles_to_store if item.get('source_type', '') == 'html_content')
                custom_count = sum(1 for item in articles_to_store if item.get('source_type', '').startswith('custom'))

                if sitemap_count:
                    logger.info(f"Sitemap items: {sitemap_count}")
                if html_count:
                    logger.info(f"HTML content items: {html_count}")
                if custom_count:
                    logger.info(f"Custom crawled items: {custom_count}")
            except Exception as e:
                logger.error(f"Error inserting documents: {str(e)}")
                # Try inserting one by one to identify problematic documents
                successful_inserts = 0
                for item in articles_to_store:
                    try:
                        collection.insert_one(item)
                        successful_inserts += 1
                    except Exception as individual_error:
                        logger.error(f"Error inserting individual document: {str(individual_error)}")
                        logger.debug(f"Problematic document: {item}")
                logger.info(f"Inserted {successful_inserts} documents individually.")
        else:
            logger.info("No valid documents to insert.")

    except ConnectionFailure:
        logger.error("Failed to connect to MongoDB")
    except ServerSelectionTimeoutError:
        logger.error("MongoDB server selection timeout")
    except Exception as e:
        logger.error(f"Unexpected error in store_data_in_mongodb: {str(e)}")
    finally:
        if client:
            try:
                client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {str(e)}")

