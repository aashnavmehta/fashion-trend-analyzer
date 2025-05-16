import os
from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app(test_config=None):
    """
    Flask application factory function.
    Creates and configures the Flask application.
    """
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Set default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DATABASE=os.path.join(app.instance_path, 'fashion_trends.sqlite'),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return "Page not found", 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return "Internal server error", 500

    return app

