# app.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    load_dotenv()

    app = Flask(__name__)

    # --- Config ---
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", os.urandom(32)),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///frood.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.getenv("UPLOAD_FOLDER", "uploads"),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # 10 MB uploads
        SESSION_COOKIE_SECURE=bool(int(os.getenv("SESSION_COOKIE_SECURE", "0"))),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        WTF_CSRF_ENABLED=True,
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # --- Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)

    # --- Models import AFTER db.init_app to avoid circulars ---
    from models import Filiale  # noqa: F401

    # --- Blueprints ---
    from blueprints.auth import auth as auth_bp
    from blueprints.bestellen import bestellen as order_bp
    from blueprints.admin import admin as admin_bp
    from blueprints.artikel import artikel as product_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(order_bp, url_prefix="/order")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(product_bp, url_prefix="/products")

    # --- No-cache for dynamic pages (tune per route if needed) ---
    @app.after_request
    def add_no_cache_headers(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # --- CLI helpers ---
    @app.cli.command("seed-branches")
    def seed_branches():
        """Create some example branches."""
        from models import Filiale
        examples = [("1010", "Zentrale"), ("1020", "Filiale Leopoldstadt"), ("1030", "Filiale Landstraße")]
        for plz, name in examples:
            if not Filiale.query.filter_by(plz=plz).first():
                db.session.add(Filiale(plz=plz, name=name))
        db.session.commit()
        print("Seeded branches.")

    return app

# For gunicorn: `gunicorn 'app:create_app()'`
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
