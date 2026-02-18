from flask import Flask
from routes import init_routes
from db import init_db
import os

app = Flask(__name__)

# Configure secret key for sessions
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database connection with retry
init_db()

# Initialize routes
init_routes(app)

if __name__ == "__main__":
    print("[*] Starting vulnerable application on port 8080")
    app.run(host="0.0.0.0", port=8080, debug=True)
