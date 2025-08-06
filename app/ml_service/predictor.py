# app/ml_service/predictor.py
import joblib
from app.utils.text_cleaner import clean_email_text
import threading
import numpy as np
from sklearn.naive_bayes import MultinomialNB

class PredictorService:
    """
    A service class to encapsulate the machine learning model and vectorizer.
    This version correctly handles adding new classes for online learning.
    """
    def __init__(self, model_path: str, vectorizer_path: str):
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self.lock = threading.Lock()
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
        if not self.model or not self.vectorizer:
            return "Model not loaded"
        cleaned_text = clean_email_text(raw_text)
        vectorized_text = self.vectorizer.transform([cleaned_text])
        prediction = self.model.predict(vectorized_text)
        return prediction[0]

    def learn(self, raw_text: str, correct_label: str):
        """
        Updates the in-memory model with a new, corrected example.
        This version correctly handles the addition of new classes by rebuilding the model.
        """
        if not self.model or not self.vectorizer:
            return False, "Model not loaded"

        with self.lock:
            cleaned_text = clean_email_text(raw_text)
            vectorized_text = self.vectorizer.transform([cleaned_text])
            
            # Check if the label is new AND if the model has been trained at least once
            if correct_label not in self.model.classes_ and hasattr(self.model, 'class_count_'):
                
                # 1. Get current model state
                old_class_count = self.model.class_count_
                old_feature_count = self.model.feature_count_
                
                # This line fixes the NameError
                new_classes = list(self.model.classes_) + [correct_label]
                
                # 2. Create a new model instance
                new_model = MultinomialNB(alpha=self.model.alpha)
                new_model.classes_ = np.array(new_classes)
                
                # 3. Manually copy and resize the learned counts to fit the new model
                new_class_count = np.append(old_class_count, [0])
                new_feature_count = np.vstack([old_feature_count, np.zeros((1, old_feature_count.shape[1]))])
                
                new_model.class_count_ = new_class_count
                new_model.feature_count_ = new_feature_count
                
                # 4. Replace the old model with our new, more capable one
                self.model = new_model

            # Now, partial_fit will work correctly every time
            self.model.partial_fit(vectorized_text, [correct_label])

        return True, f"In-memory model updated. It now knows about '{correct_label}'."

    def get_known_categories(self):
        """
        Returns a list of all classes the model currently knows.
        This fixes the AttributeError.
        """
        if not self.model:
            return []
        return self.model.classes_.tolist()