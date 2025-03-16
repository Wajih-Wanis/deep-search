from flask import Blueprint, request, jsonify, redirect, url_for
from flask_jwt_extended import create_access_token, set_access_cookies
from app.services.auth_service import (
    register_user,
    login_user,
    handle_google_authorization,
    handle_google_callback
)
from app.utils.decorators import validate_json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@validate_json({
    'email': {'type': 'string', 'required': True},
    'password': {'type': 'string', 'required': True}
})
def register():
    data = request.json
    result = register_user(data['email'], data['password'])
    
    if result['success']:
        access_token = create_access_token(identity=str(result['user_id']))
        response = jsonify({
            'success': True,
            'user_id': result['user_id']
        })
        set_access_cookies(response, access_token)
        return response
    
    return jsonify(result), 400

@auth_bp.route('/login', methods=['POST'])
@validate_json({
    'email': {'type': 'string', 'required': True},
    'password': {'type': 'string', 'required': True}
})
def login():
    data = request.json
    result = login_user(data['email'], data['password'])
    if result['success']:
        response = jsonify(result)
        set_access_cookies(response, result['access_token'])
        return response
    return jsonify(result), 401

@auth_bp.route('/google/login')
def google_login():
    return redirect(handle_google_authorization())

@auth_bp.route('/google/callback')
def google_callback():
    token = handle_google_callback()
    if token:
        response = redirect(url_for('frontend.home'))  
        set_access_cookies(response, token)
        return response
    return jsonify({'success': False, 'error': 'Google login failed'}), 401