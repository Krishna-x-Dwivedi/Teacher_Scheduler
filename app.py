
import os
from flask import Flask, send_from_directory, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from backend.database import init_db
from backend.auth import auth_bp
from backend.api import api_bp
from backend.scheduler import scheduler_bp

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key')

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(scheduler_bp, url_prefix='/api')

@app.route('/')
def index():
    return render_template('index.html')

# Serve static files if needed (Flask does this automatically for 'static' folder, but just in case)
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    with app.app_context():
        init_db()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
