from app import create_app

# Instantiate the application factory
app = create_app()

if __name__ == "__main__":
    # Run the server locally in debug mode
    # Debug mode automatically restarts the server whenever you edit python code files
    app.run(host="127.0.0.1", port=5000, debug=True)