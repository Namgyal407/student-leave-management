"""Flask application entry point.  Run:  python app.py  (from backend/)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import text
from werkzeug.exceptions import HTTPException

load_dotenv()

from db import close_session, get_session  # noqa: E402
from routes import auth as auth_routes  # noqa: E402
from routes import leave_types, leaves, notifications, users  # noqa: E402


def create_app():
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    app = Flask(__name__, static_folder=frontend_dir, static_url_path="/static")
    app.json.sort_keys = False
    app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024  # attachment request cap

    origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins}})

    app.teardown_appcontext(close_session)

    from routes import attachments
    for module in (auth_routes, leaves, leave_types, notifications, users, attachments):
        app.register_blueprint(module.bp)

    @app.get("/")
    def login_page():
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/dashboard")
    def dashboard_page():
        return send_from_directory(frontend_dir, "dashboard.html")

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
