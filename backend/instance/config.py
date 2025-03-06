import os

class DevelopmentConfig:
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ai_chat_dev')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    PROPAGATE_EXCEPTIONS = True