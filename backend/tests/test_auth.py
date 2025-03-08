import unittest
from flask import json
from app import create_app
from app.extensions import db
import bcrypt
from datetime import datetime
import mongomock

class TestAuthRoutes(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['MONGO_URI'] = 'mongodb://localhost'
        self.app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.init_app(self.app)
            db.cx = mongomock.MongoClient()
            
            self.test_user = {
                'email': 'test@example.com',
                'password_hash': bcrypt.hashpw('password'.encode(), bcrypt.gensalt()).decode('utf-8'),
                'created_at': datetime.now()
            }
            db.db.users.insert_one(self.test_user)

    def tearDown(self):
        with self.app.app_context():
            db.db.users.drop()

    def test_register_success(self):
        response = self.client.post('/auth/register', json={
            'email': 'new@example.com',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json['success'])

    def test_register_duplicate_email(self):
        response = self.client.post('/auth/register', json={
            'email': 'test@example.com',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json['success'])

    def test_login_success(self):
        response = self.client.post('/auth/login', json={
            'email': 'test@example.com',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])

    def test_login_invalid_credentials(self):
        response = self.client.post('/auth/login', json={
            'email': 'test@example.com',
            'password': 'wrong'
        })
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json['success'])

if __name__ == '__main__':
    unittest.main()