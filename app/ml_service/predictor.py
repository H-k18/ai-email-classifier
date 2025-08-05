# app/ml_service/predictor.py
import joblib
from app.utils.text_cleaner import clean_email_text

class PredictorService:
    """
    A service class to encapsulate the machine learning model and vectorizer.
    It handles loading the models and making predictions.
    """
    def __init__(self, model_path: str, vectorizer_path: str):
        """
        Initializes the service by loading the model and vectorizer from disk.
        """
        try:
            self.model = joblib.load(model_path)
            self.vectorizer = joblib.load(vectorizer_path)
            print("Successfully loaded model and vectorizer.")
        except FileNotFoundError as e:
            print(f"Error loading model files: {e}")
            self.model = None
            self.vectorizer = None
        except Exception as e:
            print(f"An unexpected error occurred during model loading: {e}")
            self.model = None
            self.vectorizer = None

    def predict(self, raw_text: str) -> str:
        """
        Makes a prediction on a single piece of raw email text.
        """
        if not self.model or not self.vectorizer:
            return "Model not loaded"

        cleaned_text = clean_email_text(raw_text)
        vectorized_text = self.vectorizer.transform([cleaned_text])
        prediction = self.model.predict(vectorized_text)
        
        return prediction[0]