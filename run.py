# run.py
from app import create_app
from app.email_poller import poll_all_users # Import the new scheduler function
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from dotenv import load_dotenv

load_dotenv()
app = create_app()

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=poll_all_users, # Use the new function
        trigger="interval", 
        minutes=10, 
        id="email_poll_job"
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    app.run(host='0.0.0.0', port=5000, debug=False)