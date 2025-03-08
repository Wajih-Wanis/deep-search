import unittest
from flask import json
from app import create_app
from app.extensions import db
from flask_jwt_extended import create_access_token
from datetime import datetime
import bcrypt
import mongomock
from unittest.mock import patch

class TestAIRoutes(unittest.TestCase):
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
            self.chat_id = db.db.chats.insert_one({
                'user_id': str(user_id),
                'title': 'Test Chat',
                'created_at': datetime.utcnow()
            }).inserted_id

    def tearDown(self):
        with self.app.app_context():
            db.db.users.drop()
            db.db.chats.drop()
            db.db.messages.drop()

    @patch('app.services.ai_service.OllamaModel')
    def test_chat_endpoint(self, mock_model):
        mock_instance = mock_model.return_value
        mock_instance._run.return_value = "Mocked response"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        response = self.client.post('/ai/chat', headers=headers, json={
            'message': 'Hello',
            'chat_id': str(self.chat_id)
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['response'], "Mocked response")
        messages = db.db.messages.find({'chat_id': str(self.chat_id)})
        self.assertEqual(len(list(messages)), 2)

    @patch('app.services.ai_service.DeepSearchAgent')
    def test_deep_search(self, mock_agent):
        mock_instance = mock_agent.return_value
        mock_instance.create_graph.return_value.invoke.return_value = {
            'final_response': 'Deep results',
            'questions': ['question1', 'question2'],
            'research_results': {'key': 'value'}  
        }
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        response = self.client.post('/ai/deep-search',
                                headers=headers,
                                json={'query': 'Test topic'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('chat_id', response.json)

if __name__ == '__main__':
    unittest.main()