from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    # Cors config
    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:5173"]}}
    )

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "application": "Sketch2Solve",
        }

    return app