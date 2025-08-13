# run.py
from app import create_app
from app.email_poller import fetch_new_emails
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = create_app()

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=fetch_new_emails, trigger="interval", minutes=1)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    app.run(host='0.0.0.0', port=5000, debug=False)