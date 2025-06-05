from flask import Flask, send_file, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from datetime import datetime
from werkzeug.utils import secure_filename

# ✅ Blueprints importieren
from blueprints.auth import auth
from blueprints.bestellen import bestellen
from blueprints.admin import admin
from blueprints.artikel import artikel

# ✅ .env-Datei laden
load_dotenv()

# ✅ App konfigurieren
app = Flask(__name__)
app.secret_key = 'frood-intern-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ✅ DATABASE_URL aus Umgebungsvariablen lesen
database_url = os.getenv('DATABASE_URL')
if not database_url:
    # Fallback für lokale Entwicklung (optional)
    database_url = 'sqlite:///frood.db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ SQLAlchemy initialisieren
db = SQLAlchemy(app)

# ✅ Blueprints registrieren
app.register_blueprint(auth)
app.register_blueprint(bestellen)
app.register_blueprint(admin)
app.register_blueprint(artikel)

# ✅ Tabellenmodelle
class Filiale(db.Model):
    __tablename__ = 'filialen'
    id = db.Column(db.Integer, primary_key=True)
    plz = db.Column(db.String, unique=True)
    name = db.Column(db.String)

# ✅ Filialnamen abrufen
def get_filialname(plz):
    filiale = Filiale.query.filter_by(plz=plz).first()
    return filiale.name if filiale else "Unbekannt"

# ✅ Cache-Verhalten deaktivieren
@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ✅ Anwendung starten
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
