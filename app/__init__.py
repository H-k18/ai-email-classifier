# app/__init__.py
from flask import Flask
from .config import Config
from .ml_service.predictor import PredictorService
from .routes.main_routes import main_bp

def create_app(config_class=Config):
    """
    Application factory function. Creates and configures the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Services
    app.predictor_service = PredictorService(
        model_path=app.config['CLASSIFIER_MODEL_PATH'],
        vectorizer_path=app.config['VECTORIZER_MODEL_PATH']
    )

    # Register Blueprints (Routes)
    app.register_blueprint(main_bp)

    return app