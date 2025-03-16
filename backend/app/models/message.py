from datetime import datetime
from bson import ObjectId
from app.extensions import db

class Message:
    @classmethod
    def create(cls, chat_id, content, role, metadata=None):
        message_data = {
            'chat_id': chat_id,
            'content': content,
            'role': role,
            'metadata': metadata or {},
            'created_at': datetime.now()
        }
        result = db.db.messages.insert_one(message_data)
        return cls.get_by_id(result.inserted_id)

    @classmethod
    def get_by_id(cls, message_id):
        return db.db.messages.find_one({'_id': ObjectId(message_id)})

    @classmethod
    def get_chat_messages(cls, chat_id, limit=100):
        return list(db.db.messages.find(
            {'chat_id': chat_id},
            sort=[('created_at', 1)],
            limit=limit
        ))