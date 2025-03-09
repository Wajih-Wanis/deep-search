from bson import ObjectId
import requests
import pymongo
import logging
from pymongo import MongoClient
from datetime import datetime
from pymongo import MongoClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integration_test.log'),
        logging.StreamHandler()
    ]
)

BASE_URL = "http://localhost:5000"
MONGO_URI = "mongodb://localhost:27017/ai_chat"

def test_full_flow():
    """End-to-end test of the application workflow"""
    logger = logging.getLogger('IntegrationTest')
    
    try:
        with MongoClient(MONGO_URI) as client:
            db = client.get_database()
            db.users.delete_many({"email": "test@example.com"})
            db.chats.delete_many({})
            db.messages.delete_many({})
        logger.info("Database cleanup completed")

        logger.info("Starting registration test")
        resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={"email": "test@example.com", "password": "password"}
        )
        assert resp.status_code == 201, "Registration failed"
        logger.info(f"Registration successful: {resp.json()}")

        logger.info("Starting login test")
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": "test@example.com", "password": "password"}
        )
        assert resp.status_code == 200, "Login failed"
        token = resp.json()['access_token']
        logger.info("Login successful - JWT token acquired")

        logger.info("Starting chat creation test")
        resp = requests.post(
            f"{BASE_URL}/chats/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 201, "Chat creation failed"
        chat_id = resp.json()['id']
        logger.info(f"Chat created successfully: {chat_id}")

        logger.info("Testing regular chat endpoint")
        resp = requests.post(
            f"{BASE_URL}/ai/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "Test message",
                "chat_id": chat_id
            }
        )
        assert resp.status_code == 200, "AI chat failed"
        logger.info(f"AI response received: {resp.json()['response'][:50]}...")

        logger.info("Triggering deep search")
        deep_resp = requests.post(
            f"{BASE_URL}/ai/deep-search",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "Comprehensive AI research"}
        )
        assert deep_resp.status_code == 200, "Deep search failed"
        logger.info(f"Deep search initiated: {deep_resp.json()}")

        logger.info("Verifying database records")
        with MongoClient(MONGO_URI) as client:
            db = client.get_database()
            
            user = db.users.find_one({"email": "test@example.com"})
            assert user, "User not found in database"
            
            chat = db.chats.find_one({"_id": ObjectId(chat_id)})
            assert chat, "Chat not found in database"
            
            messages = list(db.messages.find({"chat_id": chat_id}))
            assert len(messages) >= 2, "Insufficient messages created"
            
        logger.info("All database verifications passed")

    except AssertionError as e:
        logger.error(f"Test failure: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise
    finally:
        try:
            with MongoClient(MONGO_URI) as client:
                db = client.get_database()
                db.users.delete_many({"email": "test@example.com"})
                db.chats.delete_many({})
                db.messages.delete_many({})
            logger.info("Post-test cleanup completed")
        except Exception as cleanup_error:
            logger.error(f"Cleanup failed: {str(cleanup_error)}")

if __name__ == "__main__":
    try:
        test_full_flow()
        logging.info("All integration tests passed successfully")
    except Exception:
        logging.critical("Integration test run failed")