"""
Script to demonstrate how to add specific sites to crawl with custom selectors.
This is a utility to help users configure their news bot for specific sites.
"""

import json
from site_configs import SITE_CONFIGS, GENERAL_CONFIGS

def print_available_sites():
    """Print all currently configured sites."""
    print("Currently configured sites:")
    for site_name, config in SITE_CONFIGS.items():
        print(f"  - {site_name}: {config['url']}")
    
    print("\nGeneral configurations available:")
    for config_name in GENERAL_CONFIGS.keys():
        print(f"  - {config_name}")

def add_custom_site_interactive():
    """Interactive function to add a custom site."""
    print("\nAdding a custom site...")
    site_name = input("Enter a name for the site (e.g., 'mynews'): ").strip()
    
    if site_name in SITE_CONFIGS:
        print(f"Site '{site_name}' already exists in configurations.")
        overwrite = input("Do you want to overwrite it? (y/n): ").lower() == 'y'
        if not overwrite:
            return
    
    url = input("Enter the URL of the site: ").strip()
    
    print("\nNote: You can enter multiple CSS selectors for each element, separated by commas.")
    print("Example: 'h1, .title, .headline'")
    
    title_selectors = input("Enter CSS selectors for titles (default: 'h1, h2'): ").strip()
    if not title_selectors:
        title_selectors = 'h1, h2'
    
    content_selectors = input("Enter CSS selectors for content (default: '.content, .article, .post'): ").strip()
    if not content_selectors:
        content_selectors = '.content, .article, .post'
    
    date_selectors = input("Enter CSS selectors for dates (default: '.date, .time, time'): ").strip()
    if not date_selectors:
        date_selectors = '.date, .time, time'
    
    author_selectors = input("Enter CSS selectors for authors (default: '.author, .byline'): ").strip()
    if not author_selectors:
        author_selectors = '.author, .byline'
    
    image_selectors = input("Enter CSS selectors for images (default: 'img'): ").strip()
    if not image_selectors:
        image_selectors = 'img'
    
    # Create the configuration
    new_config = {
        'url': url,
        'selectors': {
            'title': [sel.strip() for sel in title_selectors.split(',')],
            'content': [sel.strip() for sel in content_selectors.split(',')],
            'date': [sel.strip() for sel in date_selectors.split(',')],
            'author': [sel.strip() for sel in author_selectors.split(',')],
            'image': [sel.strip() for sel in image_selectors.split(',')]
        }
    }
    
    # Add to SITE_CONFIGS
    SITE_CONFIGS[site_name] = new_config
    
    # Print the configuration
    print(f"\nNew configuration for '{site_name}':")
    print(json.dumps({site_name: new_config}, indent=2))
    
    print("\nTo permanently add this site, you need to add the following configuration to site_configs.py:")
    print("\n```python")
    print(f"'{site_name}': {{")
    print(f"    'url': '{url}',")
    print("    'selectors': {")
    for key, value in new_config['selectors'].items():
        print(f"        '{key}': {value},")
    print("    }")
    print("},")
    print("```")
    
    return new_config

def get_site_config_for_url(url):
    """Get configuration for a specific URL."""
    for site_name, config in SITE_CONFIGS.items():
        if url in config['url'] or config['url'] in url:
            return site_name, config
    
    return None, None

def get_general_config(config_type):
    """Get a general configuration."""
    if config_type in GENERAL_CONFIGS:
        return GENERAL_CONFIGS[config_type]
    return None

if __name__ == "__main__":
    print("News Bot Site Configuration Utility")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Show available sites")
        print("2. Add custom site configuration")
        print("3. Get configuration by URL")
        print("4. Get general configuration")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            print_available_sites()
        elif choice == '2':
            add_custom_site_interactive()
        elif choice == '3':
            url = input("Enter a URL to check configuration for: ").strip()
            site_name, config = get_site_config_for_url(url)
            if config:
                print(f"\nFound configuration for {site_name}: {config['url']}")
                print(f"Selectors: {config['selectors']}")
            else:
                print("No specific configuration found for this URL.")
        elif choice == '4':
            print("Available general configurations:", list(GENERAL_CONFIGS.keys()))
            config_type = input("Enter configuration type: ").strip()
            config = get_general_config(config_type)
            if config:
                print(f"Selectors for '{config_type}': {config}")
            else:
                print("Configuration not found.")
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")