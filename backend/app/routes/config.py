from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.helpers import (
    json_response,
    validate_object_id,
    handle_errors,
    parse_json
)
from app.models.user import User

config_bp = Blueprint('config', __name__)

@config_bp.route('/ai', methods=['GET'])
@jwt_required()
@handle_errors
def get_ai_config():
    """Get user's AI configuration"""
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    
    return json_response({
        'providers': user.get('providers', {}),
        'model_config': user.get('config', {})
    })

@config_bp.route('/ai', methods=['PUT'])
@jwt_required()
@parse_json(schema={
    'required': ['providers', 'config'],
    'properties': {
        'providers': {'type': 'object'},
        'config': {'type': 'object'}
    }
})
@handle_errors
def update_ai_config():
    """Update user's AI configuration"""
    user_id = get_jwt_identity()
    data = request.parsed_data
    
    User.update_config(
        user_id,
        providers=data['providers'],
        config=data['config']
    )
    
    return json_response(message="AI configuration updated successfully")

@config_bp.route('/model', methods=['POST'])
@jwt_required()
@parse_json(schema={
    'required': ['model_name', 'parameters'],
    'properties': {
        'model_name': {'type': 'string'},
        'parameters': {'type': 'object'}
    }
})
@handle_errors
def set_model_parameters():
    """Set model parameters for current session"""
    user_id = get_jwt_identity()
    data = request.parsed_data
    
    User.update_model_parameters(
        user_id,
        data['model_name'],
        data['parameters']
    )
    
    return json_response(message="Model parameters updated")

@config_bp.route('/providers', methods=['GET'])
@jwt_required()
@handle_errors
def get_available_providers():
    """Get list of available AI providers"""
    return json_response({
        'providers': ['Ollama', 'OpenAI', 'HuggingFace', 'Custom']
    })