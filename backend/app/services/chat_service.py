from app.models.chat import Chat
from app.models.message import Message

def get_user_chats(user_id):
    chats = Chat.get_user_chats(user_id)
    return [{
        'id': str(chat['_id']),
        'title': chat['title'],
        'is_deep_search': chat['is_deep_search'],
        'created_at': chat['created_at']
    } for chat in chats]

def create_new_chat(user_id):
    chat = Chat.create(user_id)
    return {
        'id': str(chat['_id']),
        'title': chat['title'],
        'created_at': chat['created_at']
    }

def get_chat_messages(user_id, chat_id):
    chat = Chat.get_by_id(chat_id)
    if not chat or chat['user_id'] != user_id:
        return []
    
    messages = Message.get_chat_messages(chat_id)
    return [{
        'id': str(msg['_id']),
        'content': msg['content'],
        'role': msg['role'],
        'created_at': msg['created_at']
    } for msg in messages]

def delete_chat(user_id, chat_id):
    chat = Chat.get_by_id(chat_id)
    if not chat or chat['user_id'] != user_id:
        return {'success': False, 'error': 'Chat not found'}
    
    Chat.delete_chat(chat_id)
    return {'success': True}