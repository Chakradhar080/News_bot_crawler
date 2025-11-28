# Enhanced News Bot with MongoDB Integration

An advanced news crawler that strengthens crawling capabilities by targeting specific sites with custom selectors. Features sophisticated crawling of both sitemap.xml files and regular HTML pages, with MongoDB integration for efficient data storage and analysis.

## Features

- **Enhanced Crawling**: Crawls both sitemap.xml files and regular HTML pages
- **Targeted Site Crawling**: Uses custom selectors for specific news sites
- **Flexible Configuration**: Support for custom site configurations
- **Multithreading/Multiprocessing**: Concurrent processing for optimal performance
- **Robust Error Handling**: Comprehensive error handling and logging
- **Efficient Data Storage**: MongoDB integration with duplicate prevention
- **MongoDB Compass Support**: Ready for data visualization and analysis

## Installation

1. Ensure MongoDB is installed and running
2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Make sure MongoDB server is running (usually on localhost:27017)

## Configuration

### MongoDB Configuration
Configure the database connection in `config.py`:

```python
MONGO_URI = 'mongodb://localhost:27017'
DATABASE_NAME = 'news_sitemap'
COLLECTION_NAME = 'articles'
```

### URL List Configuration
The bot reads URLs from `nsl.txt` (one URL per line):
```
https://www.aajtak.in
https://www.indiatv.in
```

### Site-Specific Configuration
Custom selectors for different sites are defined in `site_configs.py`. The bot includes pre-configured selectors for:
- AajTak (https://www.aajtak.in)
- IndiaTV (https://www.indiatv.in)
- NDTV (https://www.ndtv.com)
- The Hindu (https://www.thehindu.com)

## Usage

### Basic Usage
```bash
python enhanced_main.py
```

### Configuration Options

The script can be configured by modifying these variables in `enhanced_main.py`:

- `use_multiprocessing`: Use multiprocessing instead of multithreading (default: False)
- `crawl_html_content`: Crawl HTML content in addition to sitemaps (default: True)
- `use_custom_selectors`: Use custom selectors for specific sites (default: True)
- `crawl_all_configured_sites`: Crawl all configured sites (default: False)

## Adding Custom Sites

To add specific sites to crawl, modify `site_configs.py`:

```python
'my_site': {
    'url': 'https://www.my-site.com',
    'selectors': {
        'title': ['h1', '.article-title', '.headline'],
        'content': ['.article-body', '.content', '.post-content'],
        'date': ['.date', '.publish-date', 'time'],
        'author': ['.author', '.byline', '.writer'],
        'image': ['.article-image img', '.featured-image img']
    }
}
```

### Selector Types Explained:
- **Title selectors**: Elements containing article headlines
- **Content selectors**: Elements containing article text
- **Date selectors**: Elements containing publication dates
- **Author selectors**: Elements containing author information
- **Image selectors**: Elements containing article images

## MongoDB Integration

### Database Structure
- **Database**: `news_sitemap`
- **Collection**: `articles`

### Data Fields
Each stored document contains:
- `url` or `loc`: The source URL
- `title`: Article title
- `content`: Article content (from HTML crawling)
- `date`: Publication date
- `author`: Author information
- `source_type`: Source type (sitemap_news, html_content, custom_crawl)
- `image_url`: Article image (for sitemap data)
- `crawled_at`: Timestamp of crawling

### Setting up MongoDB Indexes
Run the setup script to create useful indexes for query performance:
```bash
python setup_indexes.py
```

### Using MongoDB Compass

1. Install MongoDB Compass from [MongoDB Downloads](https://www.mongodb.com/products/compass)
2. Open Compass and connect to `mongodb://localhost:27017`
3. Navigate to the `news_sitemap` database and `articles` collection
4. Use the interface to browse, filter, and analyze your crawled data

## Example Queries in MongoDB Compass

After crawling, you can run queries like:
- `{ "source_type": "html_content" }` - Find all HTML crawled content
- `{ "title": { $exists: true, $ne: "" } }` - Find all items with titles
- `{ "loc": { $regex: "aajtak.in" } }` - Find all articles from AajTak
- `{ "publication_date": { $regex: "^2023" } }` - Find 2023 articles from sitemaps

## Performance Considerations

- **Threading**: Recommended for I/O-bound tasks (network requests), default 5 workers
- **Multiprocessing**: Better for CPU-intensive parsing tasks, default 4 workers
- **Timeouts**: All network operations have 30-second timeouts
- **Rate Limiting**: Built-in retry logic with exponential backoff

## Error Handling

The application includes comprehensive error handling for:
- Network timeouts and connection failures
- Invalid URLs and date formats
- Database connection issues
- XML and HTML parsing errors
- File I/O operations

## Docker Support

A Dockerfile is included for containerized deployment:
```bash
docker build -t news-bot .
docker run -d --env-file .env news-bot
```

## Troubleshooting

- **MongoDB Connection Issues**: Verify MongoDB is running and accessible
- **Crawling Errors**: Check network connectivity and URL accessibility
- **Rate Limiting**: Some sites may block excessive requests; implement delays
- **Missing Content**: Some sites may block automated requests; check robots.txt
- **Selector Issues**: Sites may update their HTML structure; update selectors accordingly