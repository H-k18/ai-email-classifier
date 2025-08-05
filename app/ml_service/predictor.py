# app/ml_service/predictor.py
import joblib
from app.utils.text_cleaner import clean_email_text
import threading

class PredictorService:
    """
    A service class to encapsulate the machine learning model and vectorizer.
    It handles loading the models, making predictions, and online learning.
    """
    def __init__(self, model_path: str, vectorizer_path: str):
        """
        Initializes the service by loading the model and vectorizer from disk.
        """
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self.lock = threading.Lock() # To prevent race conditions when saving the model
        try:
            self.model = joblib.load(self.model_path)
            self.vectorizer = joblib.load(self.vectorizer_path)
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

    def learn(self, raw_text: str, correct_label: str):
        """
        Updates the model with a new, corrected example (online learning).
        """
        if not self.model or not self.vectorizer:
            return False, "Model not loaded"

        # The model expects specific classes it was trained on
        if correct_label not in self.model.classes_:
            return False, f"Invalid label. Model only knows: {self.model.classes_}"

        cleaned_text = clean_email_text(raw_text)
        vectorized_text = self.vectorizer.transform([cleaned_text])
        
        # Use partial_fit to update the model with the new example
        # We acquire a lock to ensure that two requests don't try to
        # update and save the model at the exact same time.
        with self.lock:
            self.model.partial_fit(vectorized_text, [correct_label])
            
            # Save the updated model and vectorizer back to disk for persistence
            try:
                joblib.dump(self.model, self.model_path)
                joblib.dump(self.vectorizer, self.vectorizer_path)
            except Exception as e:
                print(f"Error saving model: {e}")
                return False, "Could not save updated model"

        return True, "Model updated successfully"