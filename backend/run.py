from app import create_app
from app.extensions import db
import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = create_app()

if __name__ == '__main__':
    try:
        with app.app_context():
            db.db.command('ping')
            logging.info("MongoDB connection successful")
    except Exception as e:
        logging.info("MongoDB connection failed:", str(e))
    
    app.run(host='0.0.0.0', port=5000,debug=True)