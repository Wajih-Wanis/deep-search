from datetime import datetime
from bson import ObjectId
from app.extensions import db

class User:
    @classmethod
    def find_by_email(cls, email: str):
        return db.db.users.find_one({'email': email})
    
    @classmethod
    def find_by_id(cls, user_id):
        return db.db.users.find_one({'_id': ObjectId(user_id)})

    @classmethod
    def update_config(cls, user_id, providers, config):
        return db.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'providers': providers,
                'config': config,
                'updated_at': datetime.now()
            }}
        )

    @classmethod
    def create(cls, email: str, password_hash: str, name: str = None):
        return db.db.users.insert_one({  
            'email': email,
            'password_hash': password_hash,
            'name': name,
            'created_at': datetime.now()
        })    
        
    @classmethod
    def update_model_parameters(cls, user_id, model_name, parameters):
        return db.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'config.model': model_name,
                'config.parameters': parameters,
                'updated_at': datetime.now()
            }}
        )