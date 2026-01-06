
import os
from flask import Flask, send_from_directory, render_template
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
from backend.database import db
from backend.auth import auth_bp
from backend.api import api_bp
from backend.scheduler import scheduler_bp
from backend import models # Import models to ensure they are registered

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Database Configuration
if os.getenv('DB_USER'):
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME', 'timetable_db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{user}:{password}@{host}/{db_name}"
else:
    # Fallback to sqlite if no env vars (e.g. for simple testing)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timetable.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key')

# Initialize DB and Migrate
db.init_app(app)
migrate = Migrate(app, db)

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(scheduler_bp, url_prefix='/api')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # We no longer need manual init_db() calls here as Flask-Migrate handles it via CLI commands.
    # However, for first run convenience without CLI:
    with app.app_context():
        db.create_all()
        
    app.run(host='0.0.0.0', port=5000, debug=True)
