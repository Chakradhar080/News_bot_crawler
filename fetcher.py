"""
Fetcher module with improved crawling capabilities for both sitemap and regular web pages.
"""

import requests
from bs4 import BeautifulSoup
import re
import xml.etree.ElementTree as ET
import time
import logging
from urllib.parse import urljoin, urlparse
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME
from pymongo import MongoClient
import urllib3

# Disable SSL warnings if needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set default headers to appear more like a real browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def read_urls_from_file(filename):
    """Read URLs from a file, ignoring empty lines and comments."""
    urls = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    urls.append(line)
        logger.info(f"Read {len(urls)} URLs from file: {filename}")
        return urls
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return []
    except Exception as e:
        logger.error(f"Error reading file {filename}: {str(e)}")
        return []


def fetch_with_retry(url, max_retries=3, timeout=30, headers=None):
    """Fetch URL with retry logic and proper headers."""
    if headers is None:
        headers = HEADERS.copy()
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, headers=headers, timeout=timeout, verify=False)
            if response.status_code == 200:
                logger.info(f"Successfully fetched {url}")
                return response
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url} on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
    return None


def fetch_robots_txt(url):
    """Fetch robots.txt for a given URL."""
    try:
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.hostname:
            logger.error(f"Invalid URL: {url}")
            return None
        robots_url = f"{parsed_url.scheme}://{parsed_url.hostname}/robots.txt"
        response = fetch_with_retry(robots_url)
        if response and response.status_code == 200:
            return response.text
        else:
            logger.warning(f"Failed to fetch robots.txt from {robots_url}")
            return None
    except Exception as e:
        logger.error(f"Error fetching robots.txt for {url}: {str(e)}")
        return None


def extract_sitemaps_from_robots(robots_txt):
    """Extract sitemap URLs from robots.txt."""
    if not robots_txt:
        return []
    # More comprehensive pattern to match sitemap entries
    pattern = re.compile(r'^Sitemap:\s*(https?://[^\s\r\n]*)', re.MULTILINE | re.IGNORECASE)
    sitemaps = pattern.findall(robots_txt)
    logger.info(f"Found {len(sitemaps)} sitemaps from robots.txt")
    return sitemaps


def fetch_and_parse_sitemap(sitemap_url):
    """Fetch and return XML content of sitemap."""
    response = fetch_with_retry(sitemap_url)
    if response:
        return response.text
    return None


def extract_news_data(xml_data):
    """Extract news data from sitemap XML."""
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        logger.error(f"Error parsing XML: {e}")
        return []

    # Define namespaces for both regular sitemap and news sitemap
    namespaces = {
        'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
        'news': 'http://www.google.com/schemas/sitemap-news/0.9',
        'xhtml': 'http://www.w3.org/1999/xhtml'
    }

    # Try to find the default namespace if the above doesn't work
    try:
        # Handle different namespace formats
        news_items = []
        
        # Look for URL elements in sitemap
        for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            process_sitemap_url(url_elem, news_items)
        
        # Also check without namespace (in case document doesn't use them properly)
        for url_elem in root.findall('.//url'):
            process_sitemap_url(url_elem, news_items, use_namespaces=False)
        
        logger.info(f"Extracted {len(news_items)} news items from sitemap")
        return news_items
        
    except Exception as e:
        logger.error(f"Error extracting news data: {str(e)}")
        return []


def process_sitemap_url(url_elem, news_items, use_namespaces=True):
    """Process a URL element from sitemap and extract news data."""
    try:
        if use_namespaces:
            loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            lastmod_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
            news_elem = url_elem.find('{http://www.google.com/schemas/sitemap-news/0.9}news')
        else:
            loc_elem = url_elem.find('loc')
            lastmod_elem = url_elem.find('lastmod')
            news_elem = url_elem.find('.//news')  # Look for news anywhere within url
        
        if loc_elem is not None:
            loc = loc_elem.text.strip() if loc_elem.text else ''
            
            # If there's news-specific data, extract it
            if news_elem is not None:
                try:
                    if use_namespaces:
                        title_elem = news_elem.find('{http://www.google.com/schemas/sitemap-news/0.9}title')
                        pub_name_elem = news_elem.find('{http://www.google.com/schemas/sitemap-news/0.9}publication/{http://www.google.com/schemas/sitemap-news/0.9}name')
                        pub_lang_elem = news_elem.find('{http://www.google.com/schemas/sitemap-news/0.9}publication/{http://www.google.com/schemas/sitemap-news/0.9}language')
                        pub_date_elem = news_elem.find('{http://www.google.com/schemas/sitemap-news/0.9}publication_date')
                        keywords_elem = news_elem.find('{http://www.google.com/schemas/sitemap-news/0.9}keywords')
                    else:
                        title_elem = news_elem.find('.//title')
                        pub_name_elem = news_elem.find('.//name')
                        pub_lang_elem = news_elem.find('.//language')
                        pub_date_elem = news_elem.find('.//publication_date')
                        keywords_elem = news_elem.find('.//keywords')
                    
                    news_item = {
                        'loc': loc,
                        'lastmod': lastmod_elem.text.strip() if lastmod_elem is not None and lastmod_elem.text else '',
                        'title': title_elem.text.strip() if title_elem is not None and title_elem.text else '',
                        'publication_name': pub_name_elem.text.strip() if pub_name_elem is not None and pub_name_elem.text else '',
                        'publication_language': pub_lang_elem.text.strip() if pub_lang_elem is not None and pub_lang_elem.text else '',
                        'publication_date': pub_date_elem.text.strip() if pub_date_elem is not None and pub_date_elem.text else '',
                        'keywords': keywords_elem.text.strip() if keywords_elem is not None and keywords_elem.text else '',
                        'source_type': 'sitemap_news'
                    }
                    news_items.append(news_item)
                except Exception as e:
                    logger.error(f"Error extracting news data from sitemap entry: {str(e)}")
            else:
                # Just extract basic URL data if no news-specific data exists
                news_item = {
                    'loc': loc,
                    'lastmod': lastmod_elem.text.strip() if lastmod_elem is not None and lastmod_elem.text else '',
                    'title': '',
                    'publication_name': '',
                    'publication_language': '',
                    'publication_date': '',
                    'keywords': '',
                    'source_type': 'sitemap_regular'
                }
                news_items.append(news_item)
    except Exception as e:
        logger.error(f"Error processing sitemap URL: {str(e)}")


def crawl_html_content(url, custom_selectors=None):
    """Crawl HTML content from a URL and extract data based on selectors."""
    if custom_selectors is None:
        # Default selectors for news websites
        custom_selectors = {
            'title': ['h1', 'h2', 'h3', '.title', '.headline', '[class*="title"]', '[class*="headline"]'],
            'content': ['.content', '.article', '.post', '.entry-content', '.story', '[class*="content"]', '[class*="article"]'],
            'date': ['.date', '.publish-date', '.timestamp', '[class*="date"]', 'time'],
            'author': ['.author', '.byline', '[class*="author"]', '[rel="author"]']
        }
    
    response = fetch_with_retry(url)
    if not response:
        return None
    
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract data based on selectors
        extracted_data = {
            'url': url,
            'title': extract_with_selectors(soup, custom_selectors['title']),
            'content': extract_with_selectors(soup, custom_selectors['content']),
            'date': extract_with_selectors(soup, custom_selectors['date']),
            'author': extract_with_selectors(soup, custom_selectors['author']),
            'source_type': 'html_content'
        }
        
        # Clean up content
        if extracted_data['content']:
            extracted_data['content'] = clean_html_content(extracted_data['content'])
        
        logger.info(f"Extracted HTML content from {url}")
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error parsing HTML from {url}: {str(e)}")
        return None


def extract_with_selectors(soup, selectors):
    """Extract content using multiple selectors."""
    for selector in selectors:
        try:
            if selector.startswith('.'):
                # Class selector
                elements = soup.find_all(class_=selector[1:])
            elif selector.startswith('#'):
                # ID selector
                elements = [soup.find(id=selector[1:])]
            elif selector.startswith('['):
                # Attribute selector
                attr = selector[1:-1].split('=')
                if len(attr) == 2:
                    attr_name = attr[0].strip()
                    attr_value = attr[1].strip().strip('"\'')
                    elements = soup.find_all(attrs={attr_name: attr_value})
                else:
                    continue
            else:
                # Tag selector
                elements = soup.find_all(selector)
            
            if elements:
                # Get the text content of the first matching element
                text = elements[0].get_text(separator=' ', strip=True)
                if text:
                    return text
        except Exception as e:
            logger.warning(f"Error using selector {selector}: {str(e)}")
            continue
    
    return ''


def clean_html_content(content):
    """Clean up extracted HTML content."""
    if not content:
        return ''
    
    # Remove extra whitespace
    import re
    content = re.sub(r'\s+', ' ', content)
    # Remove leading/trailing whitespace
    content = content.strip()
    
    return content


def crawl_links_from_page(url, max_links=50):
    """Crawl and extract all links from a webpage."""
    response = fetch_with_retry(url)
    if not response:
        return []
    
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        # Extract all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            
            # Only collect internal links (same domain)
            if same_domain(url, absolute_url):
                links.append({
                    'url': absolute_url,
                    'text': link.get_text(strip=True),
                    'title': link.get('title', ''),
                })
        
        # Limit the number of links
        links = links[:max_links]
        logger.info(f"Found {len(links)} links from {url}")
        return links
        
    except Exception as e:
        logger.error(f"Error crawling links from {url}: {str(e)}")
        return []


def same_domain(url1, url2):
    """Check if two URLs are from the same domain."""
    from urllib.parse import urlparse
    domain1 = urlparse(url1).netloc
    domain2 = urlparse(url2).netloc
    return domain1 == domain2


def crawl_with_custom_selectors(url, selectors_config):
    """Crawl a specific URL with custom selectors configuration."""
    response = fetch_with_retry(url)
    if not response:
        return None
    
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        data = {'url': url, 'crawled_at': time.time()}
        
        for field_name, selectors in selectors_config.items():
            data[field_name] = extract_with_selectors(soup, selectors)
        
        logger.info(f"Crawled {url} with custom selectors")
        return data
        
    except Exception as e:
        logger.error(f"Error crawling {url} with custom selectors: {str(e)}")
        return None