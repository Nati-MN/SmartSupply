from flask import Blueprint, render_template, request, redirect, session, flash, current_app
from db import get_db
from werkzeug.utils import secure_filename
import os

bestellen = Blueprint('bestellen', __name__)

@bestellen.route('/bestellen', methods=['GET', 'POST'])
def bestellen_view():
    if 'filiale' not in session:
        return redirect('/')

    plz = session['filiale']
    conn = get_db()
    cur = conn.cursor()

    # Alle Artikel abrufen
    cur.execute("SELECT * FROM artikel ORDER BY lieferant, tag, name")
    artikel = cur.fetchall()

    # Formular wurde abgeschickt
    if request.method == 'POST':
        kommentar = request.form.get('kommentar', '')
        file = request.files.get('datei')
        dateiname = ''
        if file and file.filename != '':
            dateiname = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], dateiname))

        for a in artikel:
            menge = request.form.get(f"menge_{a['id']}")
            erlaubt = (not a['plz'] or plz in a['plz'].split(','))

            if menge and erlaubt and menge.isdigit():
                menge_int = int(menge)
                max_menge = int(a['maxmenge']) if a['maxmenge'] else 999

                if 0 < menge_int <= max_mengse:
                    cur.execute(
                        "INSERT INTO bestellungen (plz, artikel_id, menge, kommentar, datei) VALUES (?, ?, ?, ?, ?)",
                        (plz, a['id'], menge_int, kommentar, dateiname)
                    )
                else:
                    flash(f"Ungültige Menge für Artikel: {a['name']} – erlaubt ist 1 bis {max_menge}")

        conn.commit()
        flash('Bestellung erfolgreich gespeichert!')
        return redirect('/bestellen')

    # Nur erlaubte Artikel anzeigen
    sichtbar = []
    for a in artikel:
        erlaubt = (not a['plz'] or plz in a['plz'].split(','))
        sichtbar.append({**dict(a), "erlaubt": erlaubt})

    return render_template('bestellen.html', artikel=sichtbar, plz=plz, filialname=session.get('filialname', 'Unbekannt'))
