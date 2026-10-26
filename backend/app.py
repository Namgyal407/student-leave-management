"""Flask application entry point.  Run:  python app.py  (from backend/)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text
from werkzeug.exceptions import HTTPException

load_dotenv()

from db import close_session, get_session  # noqa: E402
from routes import auth as auth_routes  # noqa: E402
from routes import leave_types, leaves, notifications, users  # noqa: E402


def create_app():
    app = Flask(__name__)
    app.json.sort_keys = False

    origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins}})

    app.teardown_appcontext(close_session)

    for module in (auth_routes, leaves, leave_types, notifications, users):
        app.register_blueprint(module.bp)

    @app.get("/api/health")
    def health():
        get_session().execute(text("SELECT 1"))
        return jsonify({"status": "ok"}), 200

    @app.errorhandler(HTTPException)
    def handle_http(e):
        return jsonify({"error": e.description}), e.code

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        app.logger.exception("Unhandled error")
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
