import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Dictionary mapping country codes to country names for UI display
COUNTRIES = {
    'ar': 'Argentina', 'au': 'Australia', 'at': 'Austria', 'be': 'Belgium',
    'br': 'Brazil', 'bg': 'Bulgaria', 'ca': 'Canada', 'cn': 'China',
    'co': 'Colombia', 'cz': 'Czech Republic', 'eg': 'Egypt', 'fr': 'France',
    'de': 'Germany', 'gr': 'Greece', 'hk': 'Hong Kong', 'hu': 'Hungary',
    'in': 'India', 'id': 'Indonesia', 'ie': 'Ireland', 'il': 'Israel',
    'it': 'Italy', 'jp': 'Japan', 'lv': 'Latvia', 'lt': 'Lithuania',
    'my': 'Malaysia', 'mx': 'Mexico', 'ma': 'Morocco', 'nl': 'Netherlands',
    'nz': 'New Zealand', 'ng': 'Nigeria', 'no': 'Norway', 'ph': 'Philippines',
    'pl': 'Poland', 'pt': 'Portugal', 'ro': 'Romania', 'ru': 'Russia',
    'sa': 'Saudi Arabia', 'rs': 'Serbia', 'sg': 'Singapore', 'sk': 'Slovakia',
    'si': 'Slovenia', 'za': 'South Africa', 'kr': 'South Korea', 'se': 'Sweden',
    'ch': 'Switzerland', 'tw': 'Taiwan', 'th': 'Thailand', 'tr': 'Turkey',
    'ua': 'Ukraine', 'ae': 'UAE', 'gb': 'United Kingdom', 'us': 'United States',
    've': 'Venezuela'
}

# Categories supported by NewsData.io
CATEGORIES = {
    'business': 'Business',
    'entertainment': 'Entertainment',
    'environment': 'Environment',
    'food': 'Food',
    'health': 'Health',
    'politics': 'Politics',
    'science': 'Science',
    'sports': 'Sports',
    'technology': 'Technology',
    'top': 'Top News',
    'world': 'World'
}

def get_available_countries():
    """Returns a list of country codes and names for UI display"""
    return COUNTRIES

def get_available_categories():
    """Returns a list of categories for UI display"""
    return CATEGORIES

def fetch_live_news(country_code='us', category=None, search_term=None, page_size=10, page=None):
    """
    Fetch live news articles from NewsData.io API.
    
    Args:
        country_code (str): Two-letter country code (ISO 3166-1)
        category (str, optional): News category (business, entertainment, health, etc.)
        search_term (str, optional): Keyword to search for
        page_size (int): Number of articles to retrieve (max 10 for free tier)
        page (str): Page token for pagination
    
    Returns:
        list: List of news articles with title, description, source, etc.
    """
    try:
        api_key = os.getenv('NEWSDATA_API_KEY')
        if not api_key:
            print("WARNING: NEWSDATA_API_KEY not found in environment variables, falling back to NewsAPI")
            return _fetch_from_newsapi(country_code, category, search_term, page_size)
            
        # Base URL and parameters for NewsData.io API
        url = 'https://newsdata.io/api/1/news'
        params = {
            'apikey': api_key,
            'size': min(page_size, 10),  # Limit to max 10 as per API free tier restrictions
        }
        
        # Add country parameter if provided
        if country_code:
            params['country'] = country_code
            
        # Add optional parameters if provided
        if category:
            params['category'] = category
        if search_term:
            params['q'] = search_term
        if page:
            params['page'] = page
            
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        news_data = response.json()
        
        if news_data.get('status') != 'success':
            error_message = news_data.get('message', 'Unknown error')
            print(f"NewsData.io API Error: {error_message}")
            # Fall back to NewsAPI if there's an error
            return _fetch_from_newsapi(country_code, category, search_term, page_size)
            
        articles = news_data.get('results', [])
        next_page = news_data.get('nextPage')
        
        # Format articles to match our application's expected structure
        formatted_articles = []
        for article in articles:
            # Extract and format date
            publish_date = article.get('pubDate', '')
            formatted_date = _format_date(publish_date)
            
            # Create structured article data
            formatted_article = {
                'title': article.get('title', 'No Title'),
                'description': article.get('description', article.get('content', 'No description available')),
                'urlToImage': article.get('image_url', 'https://via.placeholder.com/300x200?text=No+Image'),
                'url': article.get('link', '#'),
                'source': {'name': article.get('source_id', 'Unknown Source')},
                'publishedAt': publish_date,
                'formatted_date': formatted_date,
                'content': article.get('content', article.get('description', '')),
                'creator': article.get('creator', ['Unknown'])[0] if isinstance(article.get('creator'), list) else 'Unknown',
                'country': article.get('country', []),
                'category': article.get('category', []),
                'next_page': next_page
            }
            
            # Make sure all required fields are present
            formatted_articles.append(formatted_article)
        
        return formatted_articles
        
    except requests.exceptions.RequestException as e:
        print(f"NewsData.io API Request Error: {e}")
        # Fall back to NewsAPI if there's a request error
        return _fetch_from_newsapi(country_code, category, search_term, page_size)
    except Exception as e:
        print(f"Unexpected Error with NewsData.io API: {e}")
        # Fall back to NewsAPI if there's any other error
        return _fetch_from_newsapi(country_code, category, search_term, page_size)

def _fetch_from_newsapi(country_code='us', category=None, search_term=None, page_size=20):
    """Original NewsAPI fetcher as fallback"""
    try:
        api_key = os.getenv('NEWS_API_KEY')
        if not api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
            
        # Base URL and parameters
        url = 'https://newsapi.org/v2/top-headlines'
        params = {
            'apiKey': api_key,
            'pageSize': min(page_size, 100),  # Limit to max 100 as per API restrictions
            'country': country_code
        }
        
        # Add optional parameters if provided
        if category:
            params['category'] = category
        if search_term:
            params['q'] = search_term
            
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        news_data = response.json()
        
        if news_data.get('status') != 'ok':
            raise ValueError(f"API Error: {news_data.get('message', 'Unknown error')}")
            
        articles = news_data.get('articles', [])
        
        # Enhance articles with additional metadata
        for article in articles:
            # Extract date for display (format: "2023-04-19T14:30:00Z" -> "April 19, 2023")
            if 'publishedAt' in article:
                article['formatted_date'] = _format_date(article['publishedAt'])
            
            # Ensure all articles have required fields to prevent template errors
            for field in ['title', 'description', 'urlToImage', 'url']:
                if field not in article or article[field] is None:
                    article[field] = '' if field != 'urlToImage' else 'https://via.placeholder.com/300x200?text=No+Image'
                    
        return articles
        
    except requests.exceptions.RequestException as e:
        print(f"NewsAPI Request Error: {e}")
        return []
    except ValueError as e:
        print(f"Value Error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected Error with NewsAPI: {e}")
        return []

def _format_date(date_string):
    """Helper to format date strings consistently"""
    if not date_string:
        return "Unknown date"
    
    try:
        # Handle common date formats
        date_parts = date_string.split('T')[0].split('-')
        if len(date_parts) == 3:
            year, month, day = date_parts
            month_names = ["January", "February", "March", "April", "May", "June",
                          "July", "August", "September", "October", "November", "December"]
            try:
                month_name = month_names[int(month) - 1]
                return f"{month_name} {int(day)}, {year}"
            except (IndexError, ValueError):
                pass
    except Exception:
        pass
    
    return date_string  # Return original if parsing fails