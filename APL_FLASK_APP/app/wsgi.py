from app import create_app  # Replace with your actual app factory

app = create_app()  # Initialize your Flask app

if __name__ == "__main__":
    app.run()  # Optional: For local testing