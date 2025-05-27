from flask import Blueprint, render_template, request, redirect, session
from db import get_db, get_filialname
from werkzeug.security import check_password_hash  # ✅ hinzufügen

# Blueprint erstellen
auth = Blueprint('auth', __name__)

# Login-Seite (Startseite)
@auth.route('/', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verbindung zur Datenbank
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM benutzer WHERE username = ?", (username,))
        user = cur.fetchone()

        # Prüfung: Benutzername + Passwort
        if user and check_password_hash(user['passwort'], password):
            session['rolle'] = user['rolle']
            session['username'] = user['username']

            if user['rolle'] == 'admin':
                session['admin'] = True
                return redirect('/admin_matrix')

            elif user['rolle'] == 'filiale':
                session['filiale'] = user['plz']
                session['filialname'] = get_filialname(user['plz'])
                return redirect('/bestellen')

        else:
            error = 'Login fehlgeschlagen'

    return render_template('login.html', error=error)

# Logout-Funktion
@auth.route('/logout')
def logout():
    session.clear()
    return redirect('/')

from werkzeug.security import generate_password_hash  # bereits oben? sonst hinzufügen
from flask import flash

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if not session.get('admin'):
        return redirect('/')

    error = ''
    success = ''
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        rolle = request.form['rolle']
        plz = request.form['plz'] if rolle == 'filiale' else None

        conn = get_db()
        cur = conn.cursor()

        # Benutzername prüfen
        cur.execute("SELECT * FROM benutzer WHERE username = ?", (username,))
        existing = cur.fetchone()
        if existing:
            error = "Benutzername existiert bereits."
        else:
            hashed_pw = generate_password_hash(password)
            cur.execute(
                "INSERT INTO benutzer (username, passwort, rolle, plz) VALUES (?, ?, ?, ?)",
                (username, hashed_pw, rolle, plz)
            )
            conn.commit()
            success = f"Benutzer '{username}' wurde angelegt."

    return render_template('register.html', error=error, success=success)
