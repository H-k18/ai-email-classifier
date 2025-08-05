# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True will auto-reload the server when you make changes
    app.run(debug=True)