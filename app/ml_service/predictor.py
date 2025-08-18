# app/ml_service/predictor.py
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import os
import joblib
import threading
import numpy as np
from app.utils.text_cleaner import clean_email_text

# --- BASE DATA DIRECTORY ---
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

class HybridPredictorService:
    _spam_classifier = None
    _custom_classifiers = {} # A dictionary to hold a model for each user
    _lock = threading.Lock()

    @classmethod
    def initialize_spam_model(cls):
        """Loads the powerful spam model once."""
        with cls._lock:
            if cls._spam_classifier is None:
                print("Initializing Hugging Face spam model...")
                cls._spam_classifier = pipeline(
                    "text-classification",
                    model="mrm8488/bert-tiny-finetuned-sms-spam-detection"
                )
                print("Spam model initialized.")

    @classmethod
    def get_user_classifier(cls, user_id):
        """Loads or creates a custom classifier for a specific user."""
        user_id_str = str(user_id)
        with cls._lock:
            if user_id_str not in cls._custom_classifiers:
                print(f"Loading or creating custom classifier for user {user_id_str}...")
                user_folder = os.path.join(DATA_DIR, f"user_{user_id_str}")
                os.makedirs(user_folder, exist_ok=True)
                
                model_path = os.path.join(user_folder, 'custom_classifier.joblib')
                vectorizer_path = os.path.join(user_folder, 'custom_vectorizer.joblib')

                if os.path.exists(model_path) and os.path.exists(vectorizer_path):
                    model = joblib.load(model_path)
                    vectorizer = joblib.load(vectorizer_path)
                else:
                    # --- THIS IS THE FIX ---
                    # Create a brand new, completely empty model. DO NOT train it.
                    # The 'learn' function will handle the first training correctly.
                    model = MultinomialNB()
                    vectorizer = TfidfVectorizer(max_features=5000)
                    # We only fit the vectorizer so it's ready to transform text.
                    vectorizer.fit(["dummy text to initialize"])
                
                cls._custom_classifiers[user_id_str] = {
                    'model': model,
                    'vectorizer': vectorizer,
                    'model_path': model_path,
                    'vectorizer_path': vectorizer_path
                }
            return cls._custom_classifiers[user_id_str]

    @classmethod
    def predict(cls, text: str, user_id) -> str:
        """Performs the two-stage prediction."""
        if cls._spam_classifier is None:
            cls.initialize_spam_model()

        try:
            # --- Stage 1: Spam Expert ---
            spam_result = cls._spam_classifier(text, truncation=True, max_length=512)[0]['label']
            if spam_result.lower() == 'spam':
                return 'spam'

            # --- Stage 2: Custom Learner ---
            user_classifier = cls.get_user_classifier(user_id)
            model = user_classifier['model']
            
            # --- THIS IS THE FIX ---
            # If the model has never been trained, it won't have the 'classes_' attribute.
            # In this case, we can safely default to 'primary'.
            if not hasattr(model, 'classes_'):
                return 'primary'

            cleaned_text = clean_email_text(text)
            vectorized_text = user_classifier['vectorizer'].transform([cleaned_text])
            
            prediction = model.predict(vectorized_text)
            return prediction[0]
        except Exception as e:
            print(f"Error during prediction: {e}")
            return "error"

    @classmethod
    def learn(cls, text: str, correct_label: str, user_id):
        """Updates the user's personal custom classifier."""
        if correct_label == 'spam':
            return True, "Correction noted. Spam model is pre-trained."

        user_classifier = cls.get_user_classifier(user_id)
        model = user_classifier['model']
        vectorizer = user_classifier['vectorizer']
        
        cleaned_text = clean_email_text(text)
        vectorized_text = vectorizer.transform([cleaned_text])

        with cls._lock:
            # This logic correctly handles the first training call and all subsequent calls.
            all_classes = np.unique(np.append(getattr(model, 'classes_', []), correct_label))
            model.partial_fit(vectorized_text, [correct_label], classes=all_classes)
            
            joblib.dump(model, user_classifier['model_path'])
            joblib.dump(vectorizer, user_classifier['vectorizer_path'])

        return True, f"Custom model updated. It now knows about '{correct_label}'."