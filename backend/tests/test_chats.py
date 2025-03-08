import unittest
from flask import json
from app import create_app
from app.extensions import db
from flask_jwt_extended import create_access_token
from datetime import datetime
import bcrypt
import mongomock

class TestChatRoutes(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['MONGO_URI'] = 'mongodb://localhost'
        self.app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.init_app(self.app)
            db.cx = mongomock.MongoClient()
            
            user_id = db.db.users.insert_one({
                'email': 'test@example.com',
                'password_hash': bcrypt.hashpw('password'.encode(), bcrypt.gensalt()).decode('utf-8'),
                'created_at': datetime.utcnow()
            }).inserted_id
            self.access_token = create_access_token(identity=str(user_id))
            self.user_id = user_id

    def tearDown(self):
        with self.app.app_context():
            db.db.users.drop()
            db.db.chats.drop()
            db.db.messages.drop()

    def test_create_chat(self):
        headers = {'Authorization': f'Bearer {self.access_token}'}
        response = self.client.post('/chats/', headers=headers)
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.json)

    def test_get_user_chats(self):
        headers = {'Authorization': f'Bearer {self.access_token}'}
        db.db.chats.insert_one({
            'user_id': str(self.user_id),
            'title': 'Test Chat',
            'is_deep_search': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })
        response = self.client.get('/chats/', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)

    def test_delete_chat(self):
        headers = {'Authorization': f'Bearer {self.access_token}'}
        chat_id = db.db.chats.insert_one({
            'user_id': str(self.user_id),
            'title': 'Test Chat',
            'created_at': datetime.now()
        }).inserted_id
        response = self.client.delete(f'/chats/{chat_id}', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])

if __name__ == '__main__':
    unittest.main()