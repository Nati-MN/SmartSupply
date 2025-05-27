from werkzeug.security import generate_password_hash
import sqlite3

# Verbindung zur frood.db
conn = sqlite3.connect('frood.db')
cur = conn.cursor()

# Neues Passwort vergeben
neues_passwort = 'admin123'
gehasht = generate_password_hash(neues_passwort)

# Passwort für alle Admin-Benutzer setzen
cur.execute("UPDATE benutzer SET passwort = ? WHERE rolle = 'admin'", (gehasht,))
conn.commit()
conn.close()

print(f"✅ Admin-Passwort wurde erfolgreich auf '{neues_passwort}' gesetzt.")
