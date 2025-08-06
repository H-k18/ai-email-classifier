# app/ml_service/model_provider.py
from app.ml_service.predictor import PredictorService
from app.config import Config

# This is the key: The service is instantiated ONCE when this module is first imported.
# It lives for the entire duration of the application process, guaranteeing a single state.
print("Creating a single, persistent PredictorService instance...")
predictor_instance = PredictorService(
    model_path=Config.CLASSIFIER_MODEL_PATH,
    vectorizer_path=Config.VECTORIZER_MODEL_PATH
)
print("PredictorService instance created.")