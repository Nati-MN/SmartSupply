import sqlite3

def get_db():
    conn = sqlite3.connect('frood.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_filialname(plz):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM filialen WHERE plz = ?", (plz,))
    result = cur.fetchone()
    return result["name"] if result else "Unbekannt"
