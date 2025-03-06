from datetime import datetime
from bson import ObjectId
from app.extensions import db

class User:
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
                'updated_at': datetime.utcnow()
            }}
        )

    @classmethod
    def update_model_parameters(cls, user_id, model_name, parameters):
        return db.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'config.model': model_name,
                'config.parameters': parameters,
                'updated_at': datetime.utcnow()
            }}
        )