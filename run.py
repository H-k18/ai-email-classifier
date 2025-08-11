# run.py
from app import create_app
from app.email_poller import fetch_new_emails
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

app = create_app()

# --- Setup the background scheduler ---
if __name__ == '__main__':
    # Run the email check once immediately on startup
    print("Performing initial email check on startup...")
    fetch_new_emails()
    
    # Create a scheduler that will run in the background
    scheduler = BackgroundScheduler()
    
    # Schedule the function to run every 5 minutes instead of 1
    scheduler.add_job(func=fetch_new_emails, trigger="interval", minutes=5)
    
    # Start the scheduler
    scheduler.start()
    
    # Ensure the scheduler is shut down when the app exits
    atexit.register(lambda: scheduler.shutdown())
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)