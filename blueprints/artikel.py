from flask import Blueprint, render_template, request, redirect, session
from db import get_db
from db import get_db, get_filialname

artikel = Blueprint('artikel', __name__)

@artikel.route('/artikelverwaltung', methods=['GET', 'POST'])
def artikelverwaltung():
    if not session.get('admin'):
        return redirect('/')
    
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST' and 'hinzu' in request.form:
        name = request.form['name']
        lieferant = request.form['lieferant']
        tag = request.form['tag']
        maxmenge = request.form['maxmenge']
        plz = request.form.get('plz', '')
        cur.execute("INSERT INTO artikel (name, lieferant, tag, maxmenge, plz) VALUES (?, ?, ?, ?, ?)",
                    (name, lieferant, tag, maxmenge, plz))
        conn.commit()

    if request.method == 'POST' and 'loeschen' in request.form:
        art_id = request.form['art_id']
        cur.execute("DELETE FROM artikel WHERE id = ?", (art_id,))
        conn.commit()

    cur.execute("SELECT * FROM artikel ORDER BY lieferant, tag, name")
    artikel = cur.fetchall()
    return render_template('artikelverwaltung.html', artikel=artikel)

@artikel.route('/filialverwaltung', methods=['GET', 'POST'])
def filialverwaltung():
    if not session.get('admin'):
        return redirect('/')

    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST' and 'filialhinzu' in request.form:
        plz = request.form['plz']
        name = request.form['name']
        cur.execute("INSERT INTO filialen (plz, name) VALUES (?, ?)", (plz, name))
        conn.commit()

    if request.method == 'POST' and 'filialloeschen' in request.form:
        plz = request.form['plz_loeschen']
        cur.execute("DELETE FROM filialen WHERE plz = ?", (plz,))
        conn.commit()

    cur.execute("SELECT * FROM filialen ORDER BY plz")
    filialen = cur.fetchall()
    return render_template('filialverwaltung.html', filialen=filialen)
