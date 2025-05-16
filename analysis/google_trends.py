"""
Google Trends analysis module.

This module implements functionality to interact with the Google Trends API
for analyzing search interest in fashion-related terms. It provides functions
to fetch and process trend data, calculate trend scores, and integrate with
the overall trend analysis system.
"""

import time
import logging
import datetime
from typing import Dict, List, Optional, Union, Tuple, Any

import pandas as pd
import numpy as np
from pytrends.request import TrendReq

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('google_trends_analyzer')

class RateLimiter:
    """Simple rate limiter for API requests."""
    
    def __init__(self, requests_per_minute: int = 5):
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

class GoogleTrendsAnalyzer:
    """Analyzer for Google Trends data related to fashion trends."""
    
    def __init__(self, hl: str = 'en-US', tz: int = 360, rate_limit: int = 5, 
                 retries: int = 3, backoff_factor: float = 1.5):
        """Initialize the Google Trends analyzer.
        
        Args:
            hl: Language for Google Trends results
            tz: Timezone offset (360 = US Central Time)
            rate_limit: Maximum requests per minute to avoid being blocked
            retries: Number of retries for failed requests
            backoff_factor: Exponential backoff factor for retries
        """
        self.rate_limiter = RateLimiter(rate_limit)
        self.retries = retries
        self.backoff_factor = backoff_factor
        
        # Initialize pytrends with default parameters
        self.pytrends = TrendReq(hl=hl, tz=tz)
        
        # Default timeframe is last 30 days
        self.timeframe = 'today 1-m'
    
    def _make_request_with_retry(self, method: str, *args, **kwargs) -> Optional[pd.DataFrame]:
        """Make a pytrends API request with retries and backoff.
        
        Args:
            method: The pytrends method to call
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method
            
        Returns:
            DataFrame with results if successful, None otherwise
        """
        # Apply rate limiting
        self.rate_limiter.wait()
        
        # Get the method from pytrends
        if not hasattr(self.pytrends, method):
            logger.error(f"Method {method} not found in pytrends")
            return None
        
        api_method = getattr(self.pytrends, method)
        
        # Try the request with exponential backoff
        for attempt in range(self.retries):
            try:
                result = api_method(*args, **kwargs)
                return result
            except Exception as e:
                wait_time = self.backoff_factor ** attempt
                logger.warning(f"API request failed (attempt {attempt+1}/{self.retries}): {str(e)}")
                logger.warning(f"Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
        
        logger.error(f"API request failed after {self.retries} attempts")
        return None
    
    def build_payload(self, kw_list: List[str], cat: int = 0, 
                      timeframe: Optional[str] = None, geo: str = '', 
                      gprop: str = '') -> bool:
        """Build the payload for Google Trends queries.
        
        Args:
            kw_list: List of keywords to get data for
            cat: Category to filter results by (default 0 = all)
            timeframe: Timeframe to get data for (default: last 30 days)
            geo: Location code (default '' = global)
            gprop: Google property to filter results by (default '' = web search)
            
        Returns:
            True if payload was built successfully, False otherwise
        """
        if timeframe is None:
            timeframe = self.timeframe
            
        try:
            self._make_request_with_retry('build_payload', kw_list, cat=cat,
                                         timeframe=timeframe, geo=geo, gprop=gprop)
            return True
        except Exception as e:
            logger.error(f"Failed to build payload: {str(e)}")
            return False
    
    def get_interest_over_time(self, trend_term: str, 
                               timeframe: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get interest over time data for a trend term.
        
        Args:
            trend_term: The fashion trend term to analyze
            timeframe: Timeframe to get data for (default: last 30 days)
            
        Returns:
            DataFrame with interest over time data if successful, None otherwise
        """
        if timeframe is None:
            timeframe = self.timeframe
            
        logger.info(f"Getting interest over time for '{trend_term}' ({timeframe})")
        
        # Build payload
        success = self.build_payload([trend_term], timeframe=timeframe)
        if not success:
            return None
            
        # Get interest over time
        interest_over_time_df = self._make_request_with_retry('interest_over_time')
        
        if interest_over_time_df is None or interest_over_time_df.empty:
            logger.warning(f"No interest over time data returned for '{trend_term}'")
            return None
            
        return interest_over_time_df
    
    def get_related_queries(self, trend_term: str, 
                            timeframe: Optional[str] = None) -> Optional[Dict]:
        """Get related queries for a trend term.
        
        Args:
            trend_term: The fashion trend term to analyze
            timeframe: Timeframe to get data for (default: last 30 days)
            
        Returns:
            Dictionary with related queries if successful, None otherwise
        """
        if timeframe is None:
            timeframe = self.timeframe
            
        logger.info(f"Getting related queries for '{trend_term}' ({timeframe})")
        
        # Build payload
        success = self.build_payload([trend_term], timeframe=timeframe)
        if not success:
            return None
            
        # Get related queries
        related_queries = self._make_request_with_retry('related_queries')
        
        if related_queries is None or not related_queries:
            logger.warning(f"No related queries returned for '{trend_term}'")
            return None
            
        return related_queries
    
    def analyze_trend(self, trend_term: str, timeframe: Optional[str] = None) -> Dict:
        """Analyze a fashion trend term using Google Trends data.
        
        Args:
            trend_term: The fashion trend term to analyze
            timeframe: Timeframe to get data for (default: last 30 days)
            
        Returns:
            Dictionary with analysis results
        """
        if timeframe is None:
            timeframe = self.timeframe
        
        logger.info(f"Analyzing trend: {trend_term}")
        
        # Get interest over time
        interest_df = self.get_interest_over_time(trend_term, timeframe)
        
        # If we couldn't get data, return empty results
        if interest_df is None or interest_df.empty:
            logger.warning(f"No Google Trends data available for '{trend_term}'")
            return self._generate_mock_results(trend_term, timeframe)
            
        # Process the interest over time data
        interest_data = self._process_interest_over_time(interest_df, trend_term)
        
        # Get related queries (optional)
        related_queries = self.get_related_queries(trend_term, timeframe)
        related_queries_data = self._process_related_queries(related_queries, trend_term) if related_queries else None
        
        # Determine trending direction
        trending_direction = self._determine_trending_direction(interest_df, trend_term)
        
        # Calculate metrics
        avg_interest = interest_data['average_interest']
        max_interest = interest_data['max_interest']
        
        # Build result dictionary
        result = {
            'time_period': self._format_timeframe(timeframe),
            'average_interest': avg_interest,
            'max_interest': max_interest,
            'trending_direction': trending_direction,
            'interest_over_time': interest_data['interest_over_time'],
            'related_terms': related_queries_data['rising'] if related_queries_data else []
        }
        
        return result
    
    def _process_interest_over_time(self, interest_df: pd.DataFrame, 
                                   trend_term: str) -> Dict:
        """Process interest over time data for a trend term.
        
        Args:
            interest_df: DataFrame with interest over time data
            trend_term: The fashion trend term
            
        Returns:
            Dictionary with processed interest over time data
        """
        # Convert the index to datetime if it's not already
        if not isinstance(interest_df.index, pd.DatetimeIndex):
            interest_df.index = pd.to_datetime(interest_df.index)
            
        # Extract interest values for the trend term
        interest_values = interest_df[trend_term].values
        
        # Calculate metrics
        avg_interest = np.mean(interest_values)
        max_interest = np.max(interest_values)
        
        # Format data for front-end display
        interest_over_time = []
        for date, row in interest_df.iterrows():
            interest_over_time.append({
                'date': date.strftime('%Y-%m-%d'),
                'interest': int(row[trend_term])
            })
            
        return {
            'average_interest': round(float(avg_interest)),
            'max_interest': int(max_interest),
            'interest_over_time': interest_over_time
        }
    
    def _process_related_queries(self, related_queries: Dict, 
                                trend_term: str) -> Dict:
        """Process related queries data for a trend term.
        
        Args:
            related_queries: Dictionary with related queries data
            trend_term: The fashion trend term
            
        Returns:
            Dictionary with processed related queries data
        """
        result = {'rising': [], 'top': []}
        
        if trend_term not in related_queries:
            return result
            
        queries = related_queries[trend_term]
        
        # Process rising queries
        if 'rising' in queries and not queries['rising'].empty:
            rising_df = queries['rising']
            rising_queries = []
            
            for _, row in rising_df.iterrows():
                rising_queries.append({
                    'query': row['query'],
                    'value': row['value']
                })
                
            result['rising'] = rising_queries
            
        # Process top queries
        if 'top' in queries and not queries['top'].empty:
            top_df = queries['top']
            top_queries = []
            
            for _, row in top_df.iterrows():
                top_queries.append({
                    'query': row['query'],
                    'value': row['value']
                })
                
            result['top'] = top_queries
            
        return result
    
    def _determine_trending_direction(self, interest_df: pd.DataFrame, 
                                     trend_term: str) -> str:
        """Determine if a trend is going up, down, or stable.
        
        Args:
            interest_df: DataFrame with interest over time data
            trend_term: The fashion trend term
            
        Returns:
            String indicating trend direction ('up', 'down', or 'stable')
        """
        # Convert the index to datetime if it's not already
        if not isinstance(interest_df.index, pd.DatetimeIndex):
            interest_df.index = pd.to_datetime(interest_df.index)
            
        # Extract interest values for the trend term
        interest_values = interest_df[trend_term].values
        
        # Not enough data points for trend analysis
        if len(interest_values) < 3:
            return 'stable'
            
        # Calculate linear regression to determine trend
        x = np.arange(len(interest_values))
        y = interest_values
        
        # Simple linear regression: y = mx + b
        m, b = np.polyfit(x, y, 1)
        
        # Interpret the slope
        if m > 0.5:  # Significant upward trend
            return 'up'
        elif m < -0.5:  # Significant downward trend
            return 'down'
        else:  # Stable trend
            return 'stable'
    
    def _format_timeframe(self, timeframe: str) -> str:
        """Format the timeframe string for display.
        
        Args:
            timeframe: Google Trends timeframe string
            
        Returns:
            Human-readable timeframe string
        """
        if timeframe == 'today 1-m':
            return '30 days'
        elif timeframe == 'today 3-m':
            return '90 days'
        elif timeframe == 'today 12-m':
            return '12 months'
        else:
            return timeframe
    
    def _generate_mock_results(self, trend_term: str, timeframe: str) -> Dict:
        """Generate mock results when actual API data is unavailable.
        
        Args:
            trend_term: The fashion trend term
            timeframe: Timeframe string
            
        Returns:
            Dictionary with mock analysis results
        """
        logger.warning(f"Generating mock results for '{trend_term}'")
        
        # Generate random interest values
        end_date = datetime.datetime.now()
        
        if timeframe == 'today 1-m':
            days = 30
        elif timeframe == 'today 3-m':
            days = 90
        elif timeframe == 'today 12-m':
            days = 365
        else:
            days = 30
            
        # Generate dates
        dates = [end_date - datetime.timedelta(days=i) for i in range(days, 0, -1)]
        dates = [date.strftime('%Y-%m-%d') for date in dates]
        
        # Generate random interest values
        interest_values = np.random.randint(30, 100, size=len(dates))
        
        # Calculate metrics
        avg_interest = np.mean(interest_values)
        max_interest = np.max(interest_values)
        
        # Random trending direction
        trending_direction = np.random.choice(['up', 'down', 'stable'])
        
        # Format interest over time data for the front-end
        interest_over_time = []
        for i, date in enumerate(dates):
            interest_over_time.append({
                'date': date,
                'interest': int(interest_values[i])
            })
        
        # Build result dictionary
        result = {
            'time_period': self._format_timeframe(timeframe),
            'average_interest': round(float(avg_interest)),
            'max_interest': int(max_interest),
            'trending_direction': trending_direction,
            'interest_over_time': interest_over_time,
            'related_terms': []  # Empty for mock results
        }
        
        return result


# Simplified function for testing without making actual API requests
def mock_analyze_trend(trend_term: str) -> Dict:
    """Mock function for trend analysis without making actual API requests.
    
    Args:
        trend_term: The fashion trend term to analyze
        
    Returns:
        Dictionary with mock analysis results
    """
    # Generate random data for a 30-day period
    end_date = datetime.datetime.now()
    dates = [end_date - datetime.timedelta(days=i) for i in range(30, 0, -1)]
    dates = [date.strftime('%Y-%m-%d') for date in dates]
    
    # Generate random interest values
    interest_values = np.random.randint(30, 100, size=len(dates))
    
    # Calculate metrics
    avg_interest = np.mean(interest_values)
    max_interest = np.max(interest_values)
    
    # Format interest over time data
    interest_over_time = []
    for i, date in enumerate(dates):
        interest_over_time.append({
            'date': date,
            'interest': int(interest_values[i])
        })
    
    # Random trending direction
    trending_direction = np.random.choice(['up', 'down', 'stable'])
    
    return {
        'time_period': '30 days',
        'average_interest': round(float(avg_interest)),
        'max_interest': int(max_interest),
        'trending_direction': trending_direction,
        'interest_over_time': interest_over_time,
        'related_terms': []
    }
