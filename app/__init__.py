"""
Reklam Analiz Web Uygulaması
"""
from flask import Flask
import os
import numpy as np
from flask.json.provider import DefaultJSONProvider
from flask_login import LoginManager
from dotenv import load_dotenv

# Load env vars
load_dotenv()

class NumpyJSONProvider(DefaultJSONProvider):
    """
    Numpy tiplerini (int64, float64) otomatik olarak Python native tiplerine çeviren JSON Provider.
    "Object of type int64 is not JSON serializable" hatasını çözer.
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def create_app():
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Custom JSON Provider'ı ayarla
    app.json = NumpyJSONProvider(app)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '../data/uploads')
    app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(__file__), '../data/output')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['OUTPUT_FOLDER'], 'final'), exist_ok=True)
    
    # Login Manager Setup
    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.init_app(app)
    
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        # Env var tabanlı basit auth
        admin_user = os.environ.get('ADMIN_USERNAME', 'admin')
        if user_id == admin_user:
            return User(id=user_id, username=user_id)
        return None
    
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
