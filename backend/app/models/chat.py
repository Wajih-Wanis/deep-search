from datetime import datetime
from bson import ObjectId
from app.extensions import db

class Chat:
    @classmethod
    def create(cls, user_id, title="New Chat", is_deep_search=False):
        chat_data = {
            'user_id': user_id,
            'title': title,
            'is_deep_search': is_deep_search,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        result = db.db.chats.insert_one(chat_data)
        return cls.get_by_id(result.inserted_id)

    @classmethod
    def get_by_id(cls, chat_id):
        return db.db.chats.find_one({'_id': ObjectId(chat_id)})

    @classmethod
    def get_user_chats(cls, user_id):
        return list(db.db.chats.find(
            {'user_id': user_id},
            sort=[('updated_at', -1)]
        ))

    @classmethod
    def delete_chat(cls, chat_id):
        result = db.db.chats.delete_one({'_id': ObjectId(chat_id)})
        return result.deleted_count > 0