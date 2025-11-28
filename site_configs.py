"""
Configuration file for specific sites with custom selectors for targeted crawling.
"""

# Configuration for specific news sites with custom selectors
SITE_CONFIGS = {
    'aajtak': {
        'url': 'https://www.aajtak.in',
        'selectors': {
            'title': ['h1', '.story-headline', '.title', 'h2'],
            'content': ['.story-element', '.description', '.articleBody', '.story'],
            'date': ['.publish-time', '.time-stamp', '.date', 'time'],
            'author': ['.author', '.written-by', '[rel="author"]', '.credit'],
            'image': ['.article-image img', '.image-container img', 'img[alt*="article"]']
        }
    },
    'indiatv': {
        'url': 'https://www.indiatv.in',
        'selectors': {
            'title': ['.title', '.heading', 'h1', 'h2'],
            'content': ['.description', '.news-detail', '.article-content', '.post-body'],
            'date': ['.time-stamp', '.date', '.publish-date', 'time'],
            'author': ['.author', '.byline', '.written-by', '[rel="author"]'],
            'image': ['.article-image img', '.news-image img', '.img-responsive']
        }
    },
    'ndtv': {
        'url': 'https://www.ndtv.com',
        'selectors': {
            'title': ['h1', '.sp-h1', '.article-title', '.post-title'],
            'content': ['.sp-cn', '.articlebody', '.article-text', '.content-text'],
            'date': ['.date', '.time-stamp', '.publish-date', '.meta-date'],
            'author': ['.author', '.written-by', '.meta-author', '[rel="author"]'],
            'image': ['.article-image img', '.img-article img', '.article-img img']
        }
    },
    'thehindu': {
        'url': 'https://www.thehindu.com',
        'selectors': {
            'title': ['h1', '.title', '.article-title', '.article-header'],
            'content': ['.article', '.article-text', '.story', '.article-content'],
            'date': ['.time', '.date', '.publish-time', 'time'],
            'author': ['.author', '.byline', '.written-by', '[rel="author"]'],
            'image': ['.article-image img', '.lead-img img', '.article-image picture img']
        }
    },
    'timesofindia': {
        'url': 'https://timesofindia.indiatimes.com',
        'selectors': {
            'title': ['h1', '.top-story', '.art-title', '.title'],
            'content': ['.story-body', '.arttext', '.Normal', '.content-body'],
            'date': ['.time_cmnt', '.article-time', '.time-stamp', 'time'],
            'author': ['.byline', '.author', '.writer', '.art-by'],
            'image': ['.article-image img', '.img-container img', '.photo', 'img[data-img-type="photo"]']
        }
    },
    'hindustantimes': {
        'url': 'https://www.hindustantimes.com',
        'selectors': {
            'title': ['h1', '.story-title', '.ht-article-title', '.headline'],
            'content': ['.story-content', '.story-element', '.cl-content', '.content'],
            'date': ['.date-time', '.story-published-time', '.timestamp', 'time'],
            'author': ['.author-name', '.author', '.written-by', '[rel="author"]'],
            'image': ['.article-image img', '.img-responsive', '.hero-image img']
        }
    },
    'republicworld': {
        'url': 'https://www.republicworld.com',
        'selectors': {
            'title': ['h1', '.article-title', '.story-title', '.headline'],
            'content': ['.description', '.story', '.article-content', '.article-body'],
            'date': ['.publish-time', '.time-stamp', '.article-time', 'time'],
            'author': ['.author', '.writer', '.byline', '[rel="author"]'],
            'image': ['.article-image img', '.img-fluid', '.image-container img']
        }
    },
    'zeenews': {
        'url': 'https://zeenews.india.com',
        'selectors': {
            'title': ['h1', '.article_title', '.heading', '.title'],
            'content': ['.article_content', '.text-justify', '.article-description', '.content'],
            'date': ['.date', '.time', '.article_time', 'time'],
            'author': ['.author-name', '.article-author', '.writer', '.byline'],
            'image': ['.article_image img', '.img-responsive', '.article-img img']
        }
    }
}

# General configuration for other sites
GENERAL_CONFIGS = {
    'news': {
        'selectors': {
            'title': ['h1', 'h2', '.title', '.headline', '[class*="title"]', '[class*="headline"]'],
            'content': ['.content', '.article', '.post', '.article-body', '.entry-content', '[class*="content"]', '[class*="article"]'],
            'date': ['.date', '.publish-date', '.timestamp', '[class*="date"]', 'time'],
            'author': ['.author', '.byline', '[class*="author"]', '[rel="author"]'],
            'image': ['.article-image img', '.img-responsive', 'img[alt*="article"]', '[class*="image"] img']
        }
    },
    'blog': {
        'selectors': {
            'title': ['h1', '.post-title', '.entry-title', '[class*="title"]'],
            'content': ['.post-content', '.entry-content', '.blog-content', '[class*="content"]'],
            'date': ['.date', '.post-date', '.entry-date', 'time'],
            'author': ['.author', '.byline', '.vcard', '[rel="author"]'],
            'image': ['.wp-post-image', '.post-image img', '[class*="image"] img']
        }
    },
    'general': {
        'selectors': {
            'title': ['h1', 'h2', '.title', '.headline', '[class*="title"]', '[class*="headline"]'],
            'content': ['.content', '.main', '.post', '.article', '.entry-content', '[id*="content"]', '[class*="content"]'],
            'date': ['.date', '.time', '[class*="date"]', '[class*="time"]', 'time'],
            'author': ['.author', '.byline', '[class*="author"]', '[rel="author"]'],
            'image': ['img[alt*="main"]', '.main-image img', 'img[alt*="article"]', '[class*="image"] img', '.featured-image img']
        }
    }
}