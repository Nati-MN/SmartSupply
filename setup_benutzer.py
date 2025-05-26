import sqlite3

conn = sqlite3.connect("frood.db")
cur = conn.cursor()

# Neue Tabelle erstellen
cur.execute("""
CREATE TABLE IF NOT EXISTS benutzer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    passwort TEXT NOT NULL,
    rolle TEXT NOT NULL,
    plz TEXT
)
""")

# Beispielbenutzer hinzufügen (nur einmal ausführen!)
users = [
    ("admin", "adminpass", "admin", None),
    ("filiale1000", "1000wurstico", "filiale", "1000"),
    ("filiale2000", "2000wurstico", "filiale", "2000")
]

for u in users:
    try:
        cur.execute("INSERT INTO benutzer (username, passwort, rolle, plz) VALUES (?, ?, ?, ?)", u)
    except sqlite3.IntegrityError:
        print(f"Benutzer {u[0]} existiert bereits.")

conn.commit()
conn.close()

print("Fertig! Tabelle 'benutzer' ist angelegt und Beispielnutzer wurden hinzugefügt.")
