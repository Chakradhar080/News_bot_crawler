# main.py with improved crawling capabilities and site-specific configurations

import threading
import multiprocessing
import time
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from fetcher import (
    read_urls_from_file,
    fetch_robots_txt,
    extract_sitemaps_from_robots,
    fetch_and_parse_sitemap,
    extract_news_data,
    crawl_html_content,
    crawl_links_from_page,
    crawl_with_custom_selectors
)
from storage import store_data_in_mongodb
from utils import update_last_fetch_time
from site_configs import SITE_CONFIGS, GENERAL_CONFIGS


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_sitemap(sitemap_url):
    """Process a single sitemap and extract news data."""
    try:
        logger.info(f"Processing sitemap: {sitemap_url}")
        xml_data = fetch_and_parse_sitemap(sitemap_url)
        if xml_data:
            news_data = extract_news_data(xml_data)
            if news_data:
                logger.info(f"Extracted {len(news_data)} news items from {sitemap_url}")
                return news_data
            else:
                logger.warning(f"No news data found in {sitemap_url}")
        else:
            logger.error(f"Failed to fetch or parse sitemap: {sitemap_url}")
    except Exception as e:
        logger.error(f"Error processing sitemap {sitemap_url}: {str(e)}")
    return []


def process_url(url):
    """Process a single URL and extract sitemaps."""
    try:
        logger.info(f"Processing URL: {url}")
        robots_txt = fetch_robots_txt(url)
        if robots_txt:
            sitemaps = extract_sitemaps_from_robots(robots_txt)
            logger.info(f"Found {len(sitemaps)} sitemaps for {url}")
            return sitemaps
        else:
            logger.warning(f"No robots.txt found for {url}")
    except Exception as e:
        logger.error(f"Error processing URL {url}: {str(e)}")
    return []


def crawl_html_content_for_url(url, custom_selectors=None):
    """Crawl HTML content for a specific URL with optional custom selectors."""
    try:
        logger.info(f"Crawling HTML content for: {url}")
        if custom_selectors:
            content_data = crawl_with_custom_selectors(url, custom_selectors)
        else:
            content_data = crawl_html_content(url)
        
        if content_data:
            # Add source type if not already set
            if 'source_type' not in content_data:
                content_data['source_type'] = 'html_content'
            logger.info(f"Successfully crawled HTML content for {url}")
            return [content_data]  # Return as list for consistency
        else:
            logger.warning(f"No content found for {url}")
    except Exception as e:
        logger.error(f"Error crawling HTML content for {url}: {str(e)}")
    return []


def process_url_with_html_crawling(url, custom_selectors=None):
    """Process a URL using both sitemap and HTML crawling approaches."""
    all_data = []
    
    # First try sitemap approach
    sitemaps = process_url(url)
    if sitemaps:
        for sitemap_url in sitemaps:
            xml_data = fetch_and_parse_sitemap(sitemap_url)
            if xml_data:
                news_data = extract_news_data(xml_data)
                all_data.extend(news_data)
    
    # Also crawl the main URL for content
    html_data = crawl_html_content_for_url(url, custom_selectors)
    all_data.extend(html_data)
    
    return all_data


def identify_site_config(url):
    """Identify which site configuration to use based on the URL."""
    for site_name, config in SITE_CONFIGS.items():
        if site_name in url.lower():
            logger.info(f"Using {site_name} configuration for {url}")
            return config['selectors']
    
    # Check for general categories
    for category, config in GENERAL_CONFIGS.items():
        if category in url.lower():
            logger.info(f"Using {category} general configuration for {url}")
            return config['selectors']
    
    # Return default selectors if no specific config found
    logger.info(f"Using default configuration for {url}")
    return None


def crawl_specific_sites(configured_sites):
    """Crawl specific sites with custom configurations."""
    all_data = []
    for site_config in configured_sites:
        url = site_config.get('url')
        selectors = site_config.get('selectors', {})
        if url and selectors:
            logger.info(f"Crawling {url} with custom selectors")
            try:
                data = crawl_with_custom_selectors(url, selectors)
                if data:
                    data['source_type'] = 'custom_crawl'
                    all_data.append(data)
                    logger.info(f"Successfully crawled {url}")
            except Exception as e:
                logger.error(f"Error crawling {url}: {str(e)}")
    return all_data


def process_urls_threaded(urls, max_workers=5, crawl_html=False, use_custom_configs=False):
    """Process URLs using threading."""
    all_data = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        if crawl_html:
            # Prepare futures with appropriate selectors
            futures = {}
            for url in urls:
                if use_custom_configs:
                    selectors = identify_site_config(url)
                    future = executor.submit(process_url_with_html_crawling, url, selectors)
                else:
                    future = executor.submit(process_url_with_html_crawling, url)
                futures[future] = url
        else:
            # Process sitemaps only
            futures = {executor.submit(process_url, url): url for url in urls}

        # Collect results from all URLs
        for future in as_completed(futures):
            url = futures[future]
            try:
                if crawl_html:
                    data = future.result()
                    all_data.extend(data)
                else:
                    sitemaps = future.result()
                    # Process sitemaps concurrently
                    future_to_sitemap = {executor.submit(process_sitemap, sitemap): sitemap for sitemap in sitemaps}
                    for sitemap_future in as_completed(future_to_sitemap):
                        sitemap = future_to_sitemap[sitemap_future]
                        try:
                            news_data = sitemap_future.result()
                            all_data.extend(news_data)
                        except Exception as e:
                            logger.error(f"Error processing sitemap {sitemap}: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")

    return all_data


def main(url_file, use_multiprocessing=False, max_workers=5, crawl_html=False,
         use_custom_configs=False, specific_sites_config=None, crawl_all_sites=False):
    """Main function with improved crawling capabilities."""
    try:
        urls = read_urls_from_file(url_file)
        if not urls:
            logger.warning("No URLs found in file")
            return

        logger.info(f"Processing {len(urls)} URLs")

        start_time = time.time()

        if use_multiprocessing:
            logger.info("Using multiprocessing")
            all_data = process_urls_multiprocessing(urls, max_workers, crawl_html, use_custom_configs)
        else:
            logger.info("Using multithreading")
            all_data = process_urls_threaded(urls, max_workers, crawl_html, use_custom_configs)

        # Process specific sites with custom configurations if provided
        if specific_sites_config:
            logger.info(f"Processing {len(specific_sites_config)} specific sites with custom configurations")
            specific_data = crawl_specific_sites(specific_sites_config)
            all_data.extend(specific_data)

        # If crawl_all_sites is enabled, crawl all configured sites
        if crawl_all_sites:
            logger.info("Crawling all configured sites")
            all_site_data = []
            for site_name, config in SITE_CONFIGS.items():
                data = crawl_with_custom_selectors(config['url'], config['selectors'])
                if data:
                    data['source_type'] = f'custom_{site_name}'
                    all_site_data.append(data)
            all_data.extend(all_site_data)

        end_time = time.time()
        logger.info(f"Processing completed in {end_time - start_time:.2f} seconds")

        if all_data:
            logger.info(f"Total items collected: {len(all_data)}")
            store_data_in_mongodb(all_data)
            update_last_fetch_time()
            logger.info("Data stored successfully")
        else:
            logger.warning("No data to store")

    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        raise


def process_urls_multiprocessing(urls, max_workers=4, crawl_html=False, use_custom_configs=False):
    """Process URLs using multiprocessing."""
    all_data = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        if crawl_html:
            # Prepare futures with appropriate selectors
            futures = {}
            for url in urls:
                if use_custom_configs:
                    selectors = identify_site_config(url)
                    future = executor.submit(process_url_with_html_crawling, url, selectors)
                else:
                    future = executor.submit(process_url_with_html_crawling, url)
                futures[future] = url
        else:
            # Process sitemaps only
            futures = {executor.submit(process_url, url): url for url in urls}

        # Collect results from all URLs
        for future in as_completed(futures):
            url = futures[future]
            try:
                if crawl_html:
                    data = future.result(timeout=60)  # 60 second timeout
                    all_data.extend(data)
                else:
                    sitemaps = future.result(timeout=60)  # 60 second timeout
                    # Process sitemaps 
                    for sitemap_url in sitemaps:
                        try:
                            news_data = process_sitemap(sitemap_url)
                            all_data.extend(news_data)
                        except Exception as e:
                            logger.error(f"Error processing sitemap {sitemap_url}: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")

    return all_data


if __name__ == "__main__":
    # url_file = input("Enter the filename containing URLs: ")
    url_file = "nsl.txt"  # Path to the current directory

    # Choose between threading and multiprocessing
    use_multiprocessing = False  # Set to True to use multiprocessing
    
    # Choose to crawl HTML content as well as sitemaps
    crawl_html_content = True  # Set to True to crawl HTML content
    
    # Use custom site configurations
    use_custom_selectors = True  # Set to True to use custom selectors based on site
    
    # Crawl all configured sites
    crawl_all_configured_sites = False  # Set to True to crawl all configured sites
    
    # Example configuration for specific sites with custom selectors
    specific_sites = [
        # Add specific sites here if needed
    ]

    try:
        main(
            url_file, 
            use_multiprocessing=use_multiprocessing, 
            crawl_html=crawl_html_content,
            use_custom_configs=use_custom_selectors,
            specific_sites_config=specific_sites,
            crawl_all_sites=crawl_all_configured_sites
        )
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")