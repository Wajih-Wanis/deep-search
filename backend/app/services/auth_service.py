import bcrypt
from flask import current_app, url_for
from flask_jwt_extended import create_access_token
from app.models.user import User
from app.extensions import oauth
from datetime import datetime, timedelta

def register_user(email: str, password: str):
    if User.find_by_email(email):
        return {'success': False, 'error': 'Email already exists'}
    
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    result = User.create(email, hashed.decode('utf-8'))
    
    return {'success': True, 'user_id': str(result.inserted_id)}


def login_user(email: str, password: str):
    user = User.find_by_email(email)
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        access_token = create_access_token(
            identity=str(user['_id']), 
            expires_delta=timedelta(days=1)
        )
        return {
            'success': True, 
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'name': user.get('name')
            },
            'access_token': access_token
        }
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
        result = User.create(
            email=user_info['email'],
            password_hash=None,
            name=user_info.get('name')
        )
        user = User.find_by_id(result.inserted_id)
    
    return create_access_token(
        identity=str(user['_id']),
        expires_delta=timedelta(days=1)
    )