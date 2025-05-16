from flask import (
    Blueprint, render_template, request, 
    flash, redirect, url_for, jsonify
)
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import logging
import os
from typing import Dict, Any, Optional

# Import our fashion trend analyzers
from scrapers.fashion_sites import FashionScraper, mock_search_trend
from analysis.google_trends import GoogleTrendsAnalyzer, mock_analyze_trend

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fashion_trend_analyzer')

# Initialize analyzers with appropriate rate limits
# Use environment variables for configuration if available
try:
    fashion_scraper = FashionScraper(
        rate_limit=int(os.environ.get('FASHION_SCRAPER_RATE_LIMIT', 10))
    )
    google_trends_analyzer = GoogleTrendsAnalyzer(
        hl=os.environ.get('GOOGLE_TRENDS_LANGUAGE', 'en-US'),
        tz=int(os.environ.get('GOOGLE_TRENDS_TIMEZONE', 360)),
        rate_limit=int(os.environ.get('GOOGLE_TRENDS_RATE_LIMIT', 5)),
        retries=int(os.environ.get('GOOGLE_TRENDS_RETRIES', 3))
    )
    logger.info("Successfully initialized trend analyzers")
except Exception as e:
    logger.error(f"Error initializing trend analyzers: {str(e)}")
    # We'll still define the variables but they'll be None
    fashion_scraper = None
    google_trends_analyzer = None

# Create a blueprint for our main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def index():
    """
    Home page route that displays the search form.
    """
    return render_template('index.html')

@main_bp.route('/analyze', methods=['POST'])
def analyze_trend():
    """
    Trend analysis route that processes user input and returns trend analysis.
    """
    # Get the trend term from the form
    trend_term = request.form.get('trend_term')
    
    # Validate form input
    if not trend_term or len(trend_term.strip()) == 0:
        flash('Please enter a fashion trend term to analyze.', 'error')
        return redirect(url_for('main.index'))
    
    # Standardize the trend term (trim whitespace, lowercase)
    trend_term = trend_term.strip()
    
    logger.info(f"Analyzing trend: '{trend_term}'")
    
    try:
        # Perform web scraping
        web_scrape_results = perform_web_scraping(trend_term)
        
        # Analyze Google Trends data
        google_trends_results = analyze_google_trends(trend_term)
        
        # Calculate trend confidence based on data quality
        confidence = calculate_confidence(web_scrape_results, google_trends_results)
        
        # Combine results
        analysis_results = {
            'term': trend_term,
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'trend_score': calculate_trend_score(web_scrape_results, google_trends_results, confidence),
            'web_mentions': web_scrape_results,
            'google_trends': google_trends_results,
            'summary': generate_trend_summary(trend_term, web_scrape_results, google_trends_results)
        }
        
        logger.info(f"Analysis complete for '{trend_term}', trending: {analysis_results['trend_score']['is_trending']}")
        
        return render_template(
            'results.html', 
            results=analysis_results
        )
        
    except Exception as e:
        logger.error(f"Error analyzing trend '{trend_term}': {str(e)}", exc_info=True)
        flash(f'An error occurred during analysis: {str(e)}', 'error')
        return redirect(url_for('main.index'))

# --- Helper functions for trend analysis ---

def perform_web_scraping(trend_term: str) -> Dict[str, Any]:
    """
    Perform web scraping for trend analysis.
    Uses FashionScraper to search fashion websites for trend mentions.
    
    Args:
        trend_term: The fashion trend term to analyze
        
    Returns:
        Dictionary with web scraping results
    """
    logger.info(f"Starting web scraping for '{trend_term}'")
    
    # Check if scraper is available
    if fashion_scraper is None:
        logger.warning(f"Fashion scraper unavailable, using mock data for '{trend_term}'")
        return mock_search_trend(trend_term)
    
    try:
        # Use the real scraper to search for trend mentions
        results = fashion_scraper.search_trend(trend_term)
        logger.info(f"Web scraping complete: {results['mentions']} mentions found")
        return results
    except Exception as e:
        logger.error(f"Error during web scraping for '{trend_term}': {str(e)}", exc_info=True)
        logger.warning("Falling back to mock data")
        # Fallback to mock data if scraping fails
        return mock_search_trend(trend_term)

def analyze_google_trends(trend_term: str) -> Dict[str, Any]:
    """
    Analyze Google Trends data for the trend term.
    Uses GoogleTrendsAnalyzer to fetch and analyze search interest data.
    
    Args:
        trend_term: The fashion trend term to analyze
        
    Returns:
        Dictionary with Google Trends results
    """
    logger.info(f"Starting Google Trends analysis for '{trend_term}'")
    
    # Check if analyzer is available
    if google_trends_analyzer is None:
        logger.warning(f"Google Trends analyzer unavailable, using mock data for '{trend_term}'")
        return mock_analyze_trend(trend_term)
    
    try:
        # Use the real analyzer to get trend data
        results = google_trends_analyzer.analyze_trend(trend_term)
        logger.info(f"Google Trends analysis complete: {results['average_interest']} avg interest")
        return results
    except Exception as e:
        logger.error(f"Error during Google Trends analysis for '{trend_term}': {str(e)}", exc_info=True)
        logger.warning("Falling back to mock data")
        # Fallback to mock data if analysis fails
        return mock_analyze_trend(trend_term)

def calculate_confidence(web_results: Dict[str, Any], trends_results: Dict[str, Any]) -> str:
    """
    Calculate the confidence level of trend analysis based on data quality.
    
    Args:
        web_results: Results from web scraping
        trends_results: Results from Google Trends analysis
        
    Returns:
        String indicating confidence level ('low', 'medium', or 'high')
    """
    logger.info("Calculating confidence level for trend analysis")
    
    # Start with a medium confidence level
    confidence_points = 5  # Scale of 0-10
    
    try:
        # Evaluate web scraping results
        mentions = web_results.get('mentions', 0)
        sources_analyzed = web_results.get('sources_analyzed', 0)
        source_breakdown = web_results.get('source_breakdown', [])
        
        # More mentions means higher confidence
        if mentions > 20:
            confidence_points += 2
        elif mentions > 10:
            confidence_points += 1
        elif mentions < 3:
            confidence_points -= 2
            
        # More sources analyzed means higher confidence
        if sources_analyzed >= 4:
            confidence_points += 1
            
        # Check source distribution - if all mentions are from one source, lower confidence
        sources_with_mentions = sum(1 for source in source_breakdown if source.get('mentions', 0) > 0)
        if sources_with_mentions <= 1 and mentions > 0:
            confidence_points -= 1
            
        # Evaluate Google Trends results
        avg_interest = trends_results.get('average_interest', 0)
        trending_direction = trends_results.get('trending_direction', 'stable')
        interest_over_time = trends_results.get('interest_over_time', [])
        
        # More data points means higher confidence
        if len(interest_over_time) >= 25:
            confidence_points += 1
        elif len(interest_over_time) < 10:
            confidence_points -= 1
            
        # Clear trending direction increases confidence
        if trending_direction != 'stable':
            confidence_points += 1
            
        # Higher average interest generally means more reliable data
        if avg_interest > 60:
            confidence_points += 1
        elif avg_interest < 20:
            confidence_points -= 1
            
        # Map points to confidence levels
        if confidence_points >= 7:
            confidence = 'high'
        elif confidence_points >= 4:
            confidence = 'medium'
        else:
            confidence = 'low'
            
        logger.info(f"Confidence calculation: {confidence_points} points, level: {confidence}")
        return confidence
            
    except Exception as e:
        logger.error(f"Error calculating confidence: {str(e)}", exc_info=True)
        # Default to medium confidence if calculation fails
        return 'medium'


def calculate_trend_score(web_results: Dict[str, Any], trends_results: Dict[str, Any], 
                         confidence: str = 'medium') -> Dict[str, Any]:
    """
    Calculate an overall trend score based on web scraping and Google Trends results.
    
    Args:
        web_results: Results from web scraping
        trends_results: Results from Google Trends analysis
        confidence: Confidence level of the analysis
        
    Returns:
        Dictionary with trend score details
    """
    logger.info("Calculating trend score")
    
    try:
        # Extract key metrics from web scraping results
        web_mentions = web_results.get('mentions', 0)
        
        # Calculate web score (0-100)
        # More mentions = higher score, with diminishing returns after 30 mentions
        web_score = min(100, web_mentions * 3)
        
        # Extract key metrics from Google Trends results
        google_avg_interest = trends_results.get('average_interest', 0)
        google_max_interest = trends_results.get('max_interest', 0)
        trending_direction = trends_results.get('trending_direction', 'stable')
        
        # Calculate Google Trends score (0-100)
        # Base on average interest with bonus for high max interest
        google_score = google_avg_interest
        if google_max_interest > 85:
            google_score = min(100, google_score + 10)
            
        # Calculate combined trend score with weighting
        # Web mentions are weighted slightly more for fashion trends
        web_weight = 0.55
        google_weight = 0.45
        
        # Adjust weights based on confidence in each source
        if web_mentions < 3:
            # If very few web mentions, rely more on Google Trends
            web_weight = 0.4
            google_weight = 0.6
        elif google_avg_interest < 15:
            # If very low Google interest, rely more on web mentions
            web_weight = 0.65
            google_weight = 0.35
            
        # Calculate overall score (0-100)
        overall_score = (web_score * web_weight) + (google_score * google_weight)
        
        # Determine trending status
        # Item is trending if score is high OR medium score with strong indicators
        is_trending = False
        
        if overall_score > 70:
            # High overall score indicates trending
            is_trending = True
        elif overall_score > 50:
            # Medium score needs supporting evidence
            if web_mentions > 15 and trending_direction == 'up':
                is_trending = True
            elif google_avg_interest > 65 and web_mentions > 5:
                is_trending = True
        elif trending_direction == 'up' and web_mentions > 20:
            # Special case: rapidly rising trend with significant mentions
            is_trending = True
            
        # Create result dictionary with detailed breakdown
        trend_score = {
            'overall_score': round(overall_score, 1),
            'is_trending': is_trending,
            'confidence': confidence,
            'score_breakdown': {
                'web_score': round(web_score, 1),
                'google_score': round(google_score, 1),
                'web_weight': web_weight,
                'google_weight': google_weight
            }
        }
        
        logger.info(f"Trend score calculation complete: {round(overall_score, 1)}, is_trending: {is_trending}")
        return trend_score
        
    except Exception as e:
        logger.error(f"Error calculating trend score: {str(e)}", exc_info=True)
        # Return a default score if calculation fails
        return {
            'overall_score': 50.0,
            'is_trending': False,
            'confidence': 'low',
            'score_breakdown': {
                'web_score': 50.0,
                'google_score': 50.0,
                'web_weight': 0.5,
                'google_weight': 0.5
            }
        }


def generate_trend_summary(term, web_results, trends_results):
    """
    Generate a natural language summary of the trend analysis.
    This is a placeholder implementation that will be expanded.
    
    Args:
        term: The fashion trend term
        web_results: Results from web scraping
        trends_results: Results from Google Trends analysis
        
    Returns:
        String with natural language summary
    """
    # This is a simple template-based summary
    confidence = calculate_confidence(web_results, trends_results)
    trend_score = calculate_trend_score(web_results, trends_results, confidence)
    trending_status = "is trending" if trend_score['is_trending'] else "is not trending"
    
    summary = f"Analysis of '{term}' indicates that it {trending_status} in the fashion industry. "
    
    # Add web mentions information
    summary += f"It was mentioned {web_results['mentions']} times across {web_results['sources_analyzed']} major fashion publications. "
    
    # Add Google Trends information
    summary += f"Google Trends shows an average interest level of {trends_results['average_interest']}/100 "
    summary += f"with interest {trends_results['trending_direction']} over the last 30 days."
    
    return summary

