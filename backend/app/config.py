import os
from dotenv import load_dotenv

# Load dotenv
base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, '..', '.env')

# 🎯 DEBUG PRINTS (Temporary)
print(f"DEBUG: Looking for .env file at: {os.path.abspath(env_path)}")
print(f"DEBUG: Does .env file exist there? {os.path.exists(env_path)}")

if os.path.exists(env_path):
    load_dotenv(env_path)

class Config:
    """Application configuration loaded from environment variables."""
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    MONGO_URI = os.getenv("MONGO_URI")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Validate
    if not MONGO_URI:
        raise ValueError("ERROR: MONGO_URI environment variable is missing!")
    if not OPENAI_API_KEY:
        raise ValueError("ERROR: OPENAI_API_KEY environment variable is missing!")
    
