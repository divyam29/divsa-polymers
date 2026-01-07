from pymongo import MongoClient
import certifi
from flask import current_app, g

def get_db():
    if 'db' not in g:
        mongo_uri = current_app.config.get('MONGODB_URI')
        if mongo_uri:
            try:
                g.mongo_client = MongoClient(
                    mongo_uri,
                    tlsCAFile=certifi.where(),
                    serverSelectionTimeoutMS=30000,
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    retryWrites=False
                )
                g.db = g.mongo_client['divsa']
            except Exception as e:
                current_app.logger.error(f"Failed to connect to MongoDB: {e}")
                g.db = None
                g.mongo_client = None
        else:
            g.db = None
            g.mongo_client = None
    return g.db

def close_db(e=None):
    mongo_client = g.pop('mongo_client', None)
    if mongo_client:
        mongo_client.close()

def init_app(app):
    app.teardown_appcontext(close_db)
