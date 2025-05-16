"""
Fashion website scraper module.

This module implements web scraping functionality for fashion websites
including Vogue and Business of Fashion. It provides functions to search
for trend terms, extract mentions, and perform basic sentiment analysis.
"""

import time
import random
import logging
import re
from typing import Dict, List, Optional, Union, Tuple

import requests
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fashion_scraper')

# List of popular fashion websites to scrape
FASHION_SITES = [
    {
        'name': 'Vogue',
        'url': 'https://www.vogue.com',
        'search_url': 'https://www.vogue.com/search?q={}',
        'article_selector': '.feed-card',
        'title_selector': '.feed-card__headline',
        'content_selector': '.content',
        'date_selector': '.content-header__publish-date'
    },
    {
        'name': 'Business of Fashion',
        'url': 'https://www.businessoffashion.com',
        'search_url': 'https://www.businessoffashion.com/search/?q={}',
        'article_selector': '.article-card',
        'title_selector': '.article-card__title',
        'content_selector': '.article__body',
        'date_selector': '.article-card__date'
    },
    {
        'name': 'Elle',
        'url': 'https://www.elle.com',
        'search_url': 'https://www.elle.com/search/?q={}',
        'article_selector': '.full-item',
        'title_selector': '.full-item-title',
        'content_selector': '.article-body',
        'date_selector': '.byline-timestamp'
    },
    {
        'name': 'Harper\'s Bazaar',
        'url': 'https://www.harpersbazaar.com',
        'search_url': 'https://www.harpersbazaar.com/search/?q={}',
        'article_selector': '.full-item',
        'title_selector': '.full-item-title',
        'content_selector': '.article-body',
        'date_selector': '.byline-timestamp'
    }
]

# User agent list to avoid detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
]

class RateLimiter:
    """Simple rate limiter for web requests."""
    
    def __init__(self, requests_per_minute: int = 10):
        """Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum number of requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.last_request_time = 0
    
    def wait(self):
        """Wait if necessary to comply with rate limits."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        min_interval = 60.0 / self.requests_per_minute
        
        if time_since_last_request < min_interval:
            sleep_time = min_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

class FashionScraper:
    """Scraper for fashion websites to find trend mentions."""
    
    def __init__(self, rate_limit: int = 10):
        """Initialize the fashion scraper.
        
        Args:
            rate_limit: Maximum requests per minute to avoid being blocked
        """
        self.rate_limiter = RateLimiter(rate_limit)
        self.session = requests.Session()
        
        # Download NLTK resources if needed
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('vader_lexicon')
        except LookupError:
            logger.info("Downloading required NLTK resources...")
            nltk.download('punkt')
            nltk.download('vader_lexicon')
        
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent string to avoid detection.
        
        Returns:
            Random user agent string
        """
        return random.choice(USER_AGENTS)
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make an HTTP request with rate limiting and error handling.
        
        Args:
            url: URL to request
            
        Returns:
            Response object if successful, None otherwise
        """
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # Apply rate limiting
        self.rate_limiter.wait()
        
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            return None
    
    def _extract_article_text(self, article_url: str, content_selector: str) -> str:
        """Extract text content from a full article.
        
        Args:
            article_url: URL of the article to scrape
            content_selector: CSS selector for the article content
            
        Returns:
            Extracted article text
        """
        response = self._make_request(article_url)
        if not response:
            return ""
        
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.select_one(content_selector)
        
        if not content:
            return ""
        
        # Extract text from paragraphs
        paragraphs = content.find_all('p')
        text = ' '.join([p.get_text().strip() for p in paragraphs])
        
        return text
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment classification ('positive', 'negative', or 'neutral')
        """
        scores = self.sentiment_analyzer.polarity_scores(text)
        compound = scores['compound']
        
        if compound >= 0.1:
            return 'positive'
        elif compound <= -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def search_trend(self, trend_term: str) -> Dict:
        """Search for a fashion trend term across fashion websites.
        
        Args:
            trend_term: Fashion trend term to search for
            
        Returns:
            Dictionary with search results and statistics
        """
        logger.info(f"Searching for trend term: {trend_term}")
        
        results = {
            'sources_analyzed': len(FASHION_SITES),
            'mentions': 0,
            'source_breakdown': []
        }
        
        for site in FASHION_SITES:
            try:
                site_results = self._search_site(site, trend_term)
                results['mentions'] += site_results['mentions']
                results['source_breakdown'].append(site_results)
            except Exception as e:
                logger.error(f"Error searching {site['name']}: {str(e)}")
                # Add empty results for this site to maintain structure
                results['source_breakdown'].append({
                    'source': site['name'],
                    'mentions': 0,
                    'sentiment': 'neutral',
                    'recent_article': None
                })
        
        return results
    
    def _search_site(self, site: Dict, trend_term: str) -> Dict:
        """Search a specific fashion site for the trend term.
        
        Args:
            site: Site configuration dictionary
            trend_term: Fashion trend term to search for
            
        Returns:
            Dictionary with site-specific search results
        """
        logger.info(f"Searching {site['name']} for: {trend_term}")
        
        search_url = site['search_url'].format(trend_term.replace(' ', '+'))
        response = self._make_request(search_url)
        
        if not response:
            return {
                'source': site['name'],
                'mentions': 0,
                'sentiment': 'neutral',
                'recent_article': None
            }
        
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.select(site['article_selector'])
        
        # Limit to first 10 articles for efficiency
        articles = articles[:10]
        
        mentions = 0
        sentiments = []
        recent_article = None
        
        for article in articles:
            # Get article title
            title_elem = article.select_one(site['title_selector'])
            if not title_elem:
                continue
                
            title = title_elem.get_text().strip()
            
            # Check if trend term appears in title
            if re.search(rf'\b{re.escape(trend_term)}\b', title, re.IGNORECASE):
                mentions += 1
                
                # Try to get article URL
                link = None
                if title_elem.parent.name == 'a':
                    link = title_elem.parent.get('href')
                else:
                    link_elem = article.find('a')
                    if link_elem:
                        link = link_elem.get('href')
                
                # Make article URL absolute if it's relative
                if link and not link.startswith(('http://', 'https://')):
                    link = site['url'] + ('' if link.startswith('/') else '/') + link
                
                if link:
                    # Get article content for sentiment analysis
                    article_text = self._extract_article_text(link, site['content_selector'])
                    if article_text:
                        sentiment = self._analyze_sentiment(article_text)
                        sentiments.append(sentiment)
                    
                    # Save the most recent article
                    if not recent_article:
                        recent_article = title
        
        # Determine overall sentiment
        overall_sentiment = 'neutral'
        if sentiments:
            positive_count = sentiments.count('positive')
            negative_count = sentiments.count('negative')
            neutral_count = sentiments.count('neutral')
            
            if positive_count > negative_count and positive_count > neutral_count:
                overall_sentiment = 'positive'
            elif negative_count > positive_count and negative_count > neutral_count:
                overall_sentiment = 'negative'
        
        return {
            'source': site['name'],
            'mentions': mentions,
            'sentiment': overall_sentiment,
            'recent_article': recent_article
        }

# Simplified version for testing without making actual requests
def mock_search_trend(trend_term: str) -> Dict:
    """Mock function for testing without making actual web requests.
    
    Args:
        trend_term: Fashion trend term to search for
        
    Returns:
        Dictionary with mock search results
    """
    sources = [
        {'name': 'Vogue', 'url': 'https://www.vogue.com'},
        {'name': 'Business of Fashion', 'url': 'https://www.businessoffashion.com'},
        {'name': 'Elle', 'url': 'https://www.elle.com'},
        {'name': 'Harper\'s Bazaar', 'url': 'https://www.harpersbazaar.com'},
    ]
    
    results = {
        'sources_analyzed': len(sources),
        'mentions': random.randint(5, 30),
        'source_breakdown': [
            {
                'source': source['name'],
                'mentions': random.randint(0, 8),
                'sentiment': random.choice(['positive', 'neutral', 'negative']),
                'recent_article': f"Latest {trend_term} trends in fashion"
            } for source in sources
        ]
    }
    
    return results

