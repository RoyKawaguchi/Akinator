from pymongo import MongoClient
from flask import current_app

db = None

def init_db(app):
    """Initializes the global MongoDB client connection."""
    global db
    mongo_uri = app.config["MONGO_URI"]
    
    try:
        # Initialize the PyMongo client using the config URI
        client = MongoClient(mongo_uri)
        
        # Extract the database name from the URI or default to 'ai_akinator'
        db_name = mongo_uri.split("/")[-1].split("?")[0]
        if not db_name:
            db_name = "ai_akinator"
            
        db = client[db_name]
        
        # Run a quick ping command to verify the connection is alive
        client.admin.command('ping')
        app.logger.info("Successfully connected to MongoDB!")
        
    except Exception as e:
        app.logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise e

def get_games_collection():
    """Helper utility to easily grab the games collection across routes."""
    if db is None:
        raise RuntimeError("Database not initialized! Call init_db(app) first.")
    return db["games"]