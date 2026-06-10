from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.database import init_db

def create_app():
    """
    Constructs, configures, and returns an active Flask application instance.
    """
    app = Flask(__name__)
    
    # 1. Load configuration attributes from config.py
    app.config.from_object(Config)
    
    # 2. Enable Cross-Origin Resource Sharing (CORS)
    # Allows your HTML/JS files to seamlessly make API requests to this backend
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 3. Initialize the global MongoDB database pool
    init_db(app)
    
    # 4. Register our game loop API routes blueprint
    from app.routes import api_bp
    app.register_blueprint(api_bp)
    
    @app.route("/health", methods=["GET"])
    def health_check():
        """Simple baseline endpoint to test if the server is running."""
        return {"status": "healthy", "message": "Game engine server is alive!"}, 200
        
    return app