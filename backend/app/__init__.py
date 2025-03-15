import logging
from flask import Flask
from flask_cors import CORS
from app.extensions import db, jwt, oauth
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure CORS with explicit settings
    CORS(
        app,
        origins="http://localhost:3000",  # Allow only your frontend origin
        supports_credentials=True,        # Enable credentials (cookies, authorization headers)
        allow_headers=["Content-Type", "Authorization"],  # Explicitly allowed headers
    )

    # Optional CORS logging (for debugging)
    cors_logger = logging.getLogger('flask_cors')
    cors_logger.setLevel(logging.INFO)
    handler = logging.FileHandler('cors.log')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    cors_logger.addHandler(handler)

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