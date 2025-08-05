# AI Email Classifier with Online Learning

This project is a smart email classification application built with Python and Flask. It uses a pre-trained Naive Bayes model to classify emails as 'primary' or 'spam' and features a real-time online learning mechanism that allows the model to learn and adapt based on user corrections.

## 🚀 Key Features

-   **Initial Prediction:** Uses a pre-trained Scikit-learn model (`.joblib` files) to provide immediate classification for new emails.
-   **Online Learning:** Implements a feedback loop where the model is updated in real-time using `partial_fit` whenever a user corrects a prediction.
-   **Web Interface:** A simple, clean user interface built with Flask and vanilla JavaScript for easy interaction.
-   **Modular Architecture:** Built using a service-oriented design pattern that separates web routes, machine learning services, and utilities for maintainability and scalability.

---

## 📂 Project Structure

The project is organized into a modular structure to keep the code clean and maintainable.


/email_classifier_app/
|
|-- app/
|   |-- ml_service/         # Core machine learning logic
|   |-- routes/             # Flask web routes (API endpoints)
|   |-- templates/          # HTML files
|   |-- utils/              # Helper functions (e.g., text cleaning)
|   |-- init.py         # Application factory
|   |-- config.py           # Configuration settings
|
|-- email_classifier.joblib # The trained classifier model
|-- vectorizer.joblib       # The TF-IDF vectorizer
|-- requirements.txt        # Python dependencies
|-- .gitignore              # Files to be ignored by Git
|-- run.py                  # Entry point to run the application
|-- README.md               # This file


---

## 🛠️ Technology Stack

-   **Backend:** Python, Flask
-   **Machine Learning:** Scikit-learn, Pandas, NLTK
-   **Frontend:** HTML, CSS, JavaScript
-   **Server:** Local Flask development server

---

## ⚙️ Getting Started

Follow these instructions to set up and run the project on your local machine.

### Prerequisites

-   Python 3.8+
-   Git
-   `pip` for package management

### Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/your-username/ai-email-classifier.git](https://github.com/your-username/ai-email-classifier.git)
    cd ai-email-classifier
    ```

2.  **Create and activate a virtual environment**
    ```bash
    # For Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Create a `requirements.txt` file**
    Create a file named `requirements.txt` in the root directory and add the following lines:
    ```
    Flask
    scikit-learn
    pandas
    nltk
    joblib
    ```

4.  **Install the required packages**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Download NLTK Stopwords**
    Run the following in a Python interpreter one time to download the necessary data for text cleaning:
    ```python
    import nltk
    nltk.download('stopwords')
    ```

6.  **Place Model Files**
    Ensure your trained model files, `email_classifier.joblib` and `vectorizer.joblib`, are placed in the root directory of the project.

### Running the Application

1.  **Start the Flask server**
    ```bash
    python run.py
    ```

2.  **View in Browser**
    Open your web browser and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🧠 How It Works

1.  **Prediction:** A user pastes raw email text into the web interface and clicks "Classify". The text is sent to the `/predict` API endpoint on the Flask server. The `PredictorService` cleans the text, vectorizes it, and uses the loaded Naive Bayes model to predict the class (`primary` or `spam`).

2.  **Learning:** If the prediction is incorrect, the user can click one of the "Correct" buttons. This sends the original email text and the `correct_label` to the `/learn` API endpoint. The `PredictorService` then uses `partial_fit` to update the model with this single new example and immediately saves the improved model back to disk.

---

## 🔮 Future Improvements

-   **User Authentication:** Add user accounts so that each user can have their own personalized, fine-tuned model.
-   **Database Integration:** Store user corrections in a database to build a more robust training set over time.
-   **Multi-Class Classification:** Allow users to create their own custom folders (e.g., 'Work', 'Family', 'Promotions') and train the model to classify emails into multiple categories.
-   **Deployment:** Containerize the application with Docker and deploy it to a cloud service like Heroku or AWS.

