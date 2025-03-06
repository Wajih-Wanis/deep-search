from flask import Flask
from flask_cors import CORS
from app.extensions import db, jwt, oauth
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    oauth.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.chats import chats_bp
    from app.routes.ai import ai_bp
    from app.routes.config import config_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chats_bp, url_prefix='/chats')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    app.register_blueprint(config_bp, url_prefix='/config')
    
    return app