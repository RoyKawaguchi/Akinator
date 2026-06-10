import os
from dotenv import load_file

# Load dotenv
base_dir = os.path.abspath(os.path.dirname(__path__ if "__path__" in locals() else __file__))
env_path = os.path.join(base_dir, '..', '.env')
if os.path.exists(env_path):
    from dotenv import load_dotenv
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
    
