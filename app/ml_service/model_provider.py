# app/ml_service/model_provider.py
from app.ml_service.predictor import HybridPredictorService

# --- THIS IS THE DEFINITIVE FIX ---
# We now correctly initialize the AI model when the application starts.
print("Initializing the AI model service...")
predictor_instance = HybridPredictorService()
predictor_instance.initialize_spam_model() # This line ensures the model is loaded
print("AI model service is ready.")