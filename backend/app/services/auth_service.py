import bcrypt
from flask import current_app, url_for
from app.models.user import User
from app.extensions import oauth
from datetime import datetime
from app.extensions import db


def register_user(email: str, password: str):
    # Check if user exists
    if User.find_by_email(email):
        return {'success': False, 'error': 'Email already exists'}
    
    # Create new user
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    result = User.create(email, hashed.decode('utf-8'))    
    result = db.users.insert_one({
        'email': email,
        'password_hash': hashed.decode('utf-8'),
        'created_at': datetime.utcnow()
    })
    
    return {'success': True, 'user_id': str(result.inserted_id)}

def login_user(email: str, password: str):
    user = User.find_by_email(email)
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return {'success': True, 'user': user}
    return {'success': False, 'error': 'Invalid credentials'}

def handle_google_authorization():
    google = oauth.create_client('google')
    return google.authorize_redirect(url_for('auth.google_callback', _external=True))

def handle_google_callback():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    if not token:
        return None
    
    user_info = google.get('userinfo').json()
    user = User.find_by_email(user_info['email'])
    
    if not user:
        user = User.create(
            email=user_info['email'],
            password_hash=None,
            name=user_info.get('name')
        )
    
    return create_access_token(identity=str(user['_id']))