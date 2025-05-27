from flask import Flask, send_file, flash, make_response
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

# ✅ Blueprint importieren
from blueprints.auth import auth
from blueprints.bestellen import bestellen
from blueprints.admin import admin
from blueprints.artikel import artikel



# ✅ App konfigurieren
app = Flask(__name__)
app.secret_key = 'frood-intern-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ✅ Blueprint registrieren
app.register_blueprint(auth)
app.register_blueprint(bestellen)
app.register_blueprint(admin)
app.register_blueprint(artikel)



# ✅ Datenbankverbindung
def get_db():
    conn = sqlite3.connect('frood.db')
    conn.row_factory = sqlite3.Row
    return conn

# ✅ Filialnamen abrufen
def get_filialname(plz):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM filialen WHERE plz = ?", (plz,))
    result = cur.fetchone()
    conn.close()
    return result["name"] if result else "Unbekannt"

# ✅ Cache-Verhalten deaktivieren
@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ✅ Hier kommen später deine anderen Blueprints:
# z. B. bestellen, admin, artikelverwaltung usw.
# Beispiel:
# from blueprints.bestellen import bestellen
# app.register_blueprint(bestellen)

# ✅ Anwendung starten
if __name__ == '__main__':
    app.run(debug=True)
