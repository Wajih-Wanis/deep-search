from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.ai_service import handle_chat, handle_deep_search

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    user_id = get_jwt_identity()
    data = request.json
    return handle_chat(user_id, data)

@ai_bp.route('/deep-search', methods=['POST'])
@jwt_required()
def deep_search():
    user_id = get_jwt_identity()
    data = request.json
    return handle_deep_search(user_id, data)