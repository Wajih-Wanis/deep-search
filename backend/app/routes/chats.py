from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.chat_service import (
    get_user_chats,
    create_new_chat,
    get_chat_messages,
    delete_chat
)

chats_bp = Blueprint('chats', __name__)

@chats_bp.route('/', methods=['GET'])
@jwt_required()
def get_chats():
    user_id = get_jwt_identity()
    chats = get_user_chats(user_id)
    return jsonify(chats)

@chats_bp.route('/', methods=['POST'])
@jwt_required()
def create_chat():
    user_id = get_jwt_identity()
    chat = create_new_chat(user_id)
    return jsonify(chat), 201

@chats_bp.route('/<chat_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(chat_id):
    user_id = get_jwt_identity()
    messages = get_chat_messages(user_id, chat_id)
    return jsonify(messages)

@chats_bp.route('/<chat_id>', methods=['DELETE'])
@jwt_required()
def remove_chat(chat_id):
    user_id = get_jwt_identity()
    result = delete_chat(user_id, chat_id)
    return jsonify(result), 200 if result['success'] else 404