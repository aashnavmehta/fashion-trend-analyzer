# Fashion Trend Analyzer

A web application that analyzes fashion trends by scraping fashion publications and integrating Google Trends data. This tool helps identify if certain colors, styles, or fashion concepts are currently trending based on multiple data sources.

![Fashion Trend Analyzer](https://via.placeholder.com/800x400?text=Fashion+Trend+Analyzer)

## Features

- **Web Scraping**: Analyzes top fashion websites including Vogue and Business of Fashion
- **Google Trends Integration**: Leverages search interest data for trend validation
- **Trend Analysis**: Combines multiple data sources to calculate trend scores
- **Sentiment Analysis**: Determines if trend mentions are positive, neutral, or negative
- **Visual Reports**: Displays trend data with interactive charts and visualizations
- **Natural Language Summaries**: Generates human-readable trend analysis reports
- **Responsive Design**: Works on desktop and mobile devices

## Installation

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- Git

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/fashion-trend-analyzer.git
   cd fashion-trend-analyzer
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root (use the provided template in `.env.example`)

5. Download NLTK resources (automatically done on first run or run manually):
   ```
   python -c "import nltk; nltk.download('punkt'); nltk.download('vader_lexicon')"
   ```

## Usage

1. Start the Flask development server:
   ```
   flask run
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

3. Enter a fashion trend term to analyze (e.g., "butter yellow", "oversized blazers", "platform shoes")

4. Review the analysis results, including:
   - Overall trend score and trending status
   - Web mentions across fashion publications
   - Google Trends data over the past 30 days
   - Natural language summary of findings

## Configuration

The application can be configured using environment variables in a `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode (development/production) | development |
| `FLASK_DEBUG` | Enable debug mode | 1 |
| `FASHION_SCRAPER_RATE_LIMIT` | Requests per minute for web scraping | 10 |
| `GOOGLE_TRENDS_RATE_LIMIT` | Requests per minute for Google Trends | 5 |
| `GOOGLE_TRENDS_LANGUAGE` | Language for Google Trends queries | en-US |
| `LOG_LEVEL` | Logging level | INFO |

## Development

### Project Structure

```
fashion-trend-analyzer/
├── app/                  # Flask application
│   ├── __init__.py       # Application factory
│   ├── routes.py         # Web routes and controllers
│   └── templates/        # HTML templates
├── scrapers/             # Web scraping modules
│   └── fashion_sites.py  # Fashion website scraper
├── analysis/             # Data analysis modules
│   └── google_trends.py  # Google Trends analyzer
├── tests/                # Test cases
├── .env                  # Environment configuration
├── .gitignore            # Git ignore file
├── main.py               # Application entry point
├── README.md             # Project documentation
└── requirements.txt      # Dependencies
```

### Running Tests

```
pytest
```

### Adding New Features

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Open a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Technology Stack

- **Backend Framework**: Flask (Python)
- **Web Scraping**: BeautifulSoup4, Requests
- **Data Analysis**: Pandas, NumPy
- **NLP**: NLTK, VADER sentiment analysis
- **Trend Data**: Google Trends API (pytrends)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Visualization**: Chart.js
- **Database**: SQLite (for future expansion)

## Acknowledgements

- Fashion data sourced from Vogue, Business of Fashion, Elle, and Harper's Bazaar
- Search interest data from Google Trends
- Icon design by [Bootstrap Icons](https://icons.getbootstrap.com/)

