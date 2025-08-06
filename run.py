# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Run the app. 
    # use_reloader=False is CRITICAL for development to prevent the server
    # from restarting and erasing the in-memory model updates.
    app.run(debug=True, use_reloader=False)
