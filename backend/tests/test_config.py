import unittest
from flask import json
from app import create_app
from app.extensions import db
from flask_jwt_extended import create_access_token
import bcrypt
from datetime import datetime
import mongomock

class TestConfigRoutes(unittest.TestCase):
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
                'providers': {'openai': False},
                'config': {'model': 'default'},
                'created_at': datetime.now()
            }).inserted_id
            self.access_token = create_access_token(identity=str(user_id))

    def tearDown(self):
        with self.app.app_context():
            db.db.users.drop()

    def test_get_ai_config(self):
        headers = {'Authorization': f'Bearer {self.access_token}'}
        response = self.client.get('/config/ai', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('providers', response.json['data'])

    def test_update_ai_config(self):
        headers = {'Authorization': f'Bearer {self.access_token}'}
        new_config = {
            'providers': {'openai': True},
            'config': {'model': 'gpt-4'}
        }
        response = self.client.put('/config/ai', headers=headers, json=new_config)
        self.assertEqual(response.status_code, 200)
        user = db.db.users.find_one()
        self.assertEqual(user['providers'], new_config['providers'])

    def test_get_providers(self):
        headers = {'Authorization': f'Bearer {self.access_token}'}
        response = self.client.get('/config/providers', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('providers', response.json['data'])

if __name__ == '__main__':
    unittest.main()