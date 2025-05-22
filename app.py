from flask import Flask, render_template, request, redirect, session, send_file, flash, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime  # ✅ HIER!



app = Flask(__name__)
app.secret_key = 'frood-intern-secret-key'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db():
    conn = sqlite3.connect('frood.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'adminpass':
            session['admin'] = True
            return redirect('/admin_matrix')
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM filialen WHERE plz = ?", (username,))
        filiale = cur.fetchone()
        if filiale and password == filiale['plz'] + 'wurstico':
            session['filiale'] = filiale['plz']
            session['filialname'] = filiale['name']
            return redirect('/bestellen')
        else:
            error = 'Login fehlgeschlagen'
    return render_template('login.html', error=error)

@app.route('/bestellen', methods=['GET', 'POST'])
def bestellen():
    if 'filiale' not in session:
        return redirect('/')
    plz = session['filiale']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM artikel ORDER BY lieferant, tag, name")
    artikel = cur.fetchall()
    if request.method == 'POST':
        kommentar = request.form.get('kommentar', '')
        file = request.files.get('datei')
        dateiname = ''
        if file and file.filename != '':
            dateiname = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], dateiname))
        for a in artikel:
            menge = request.form.get(f'menge_{a["id"]}')
            erlaubt = (not a['plz'] or plz in a['plz'].split(','))
            if menge and erlaubt and menge.isdigit() and int(menge) > 0:
                cur.execute("INSERT INTO bestellungen (plz, artikel_id, menge, kommentar, datei) VALUES (?, ?, ?, ?, ?)",
                            (plz, a['id'], menge, kommentar, dateiname))
        conn.commit()
        flash('Bestellung erfolgreich gespeichert!')
        return redirect('/bestellen')
    sichtbar = []
    for a in artikel:
        erlaubt = (not a['plz'] or plz in a['plz'].split(','))
        sichtbar.append({**dict(a), "erlaubt": erlaubt})
    return render_template('bestellen.html', artikel=sichtbar, plz=plz, filialname=session['filialname'])

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.*, f.name as filialname, a.name as artikelname, a.lieferant, a.tag
        FROM bestellungen b
        JOIN filialen f ON f.plz = b.plz
        JOIN artikel a ON a.id = b.artikel_id
        ORDER BY b.zeitpunkt DESC
    """)
    bestellungen = cur.fetchall()
    return render_template('admin.html', bestellungen=bestellungen)

@app.route('/artikelverwaltung', methods=['GET', 'POST'])
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

@app.route('/filialverwaltung', methods=['GET', 'POST'])
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

@app.route('/uploads/<filename>')
def uploads(filename):
    if not session.get('admin'):
        return redirect('/')
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/admin_matrix')
def admin_matrix():
    if not session.get('admin'):
        return redirect('/')

    conn = get_db()
    cur = conn.cursor()

    # Alle Filialen
    cur.execute("SELECT * FROM filialen ORDER BY plz")
    filialen = cur.fetchall()

    # Alle Artikel
    cur.execute("SELECT * FROM artikel ORDER BY lieferant, tag, name")
    artikel_raw = cur.fetchall()

    # Alle Bestellungen gruppieren
    cur.execute("SELECT artikel_id, plz, SUM(menge) as summe FROM bestellungen GROUP BY artikel_id, plz")
    bestellungen_raw = cur.fetchall()

    # Matrix vorbereiten
    bestell_matrix = {}
    for row in bestellungen_raw:
        aid = row['artikel_id']
        if aid not in bestell_matrix:
            bestell_matrix[aid] = {}
        bestell_matrix[aid][row['plz']] = row['summe']

    # Struktur für HTML
    artikel_liste = []
    for art in artikel_raw:
        artikel_liste.append({
            "id": art["id"],
            "name": art["name"],
            "lieferant": art["lieferant"],
            "tag": art["tag"],
            "bestellungen": bestell_matrix.get(art["id"], {})
        })

    return render_template("admin_matrix.html", artikel_liste=artikel_liste, filialen=filialen, current_date=datetime.today().strftime('%d.%m.%Y'))

@app.route('/admin_matrix_export/<format>')
def admin_matrix_export(format):
    if not session.get('admin'):
        return redirect('/')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM filialen ORDER BY plz")
    filialen = cur.fetchall()
    cur.execute("SELECT * FROM artikel ORDER BY lieferant, tag, name")
    artikel_raw = cur.fetchall()
    cur.execute("SELECT artikel_id, plz, SUM(menge) as summe FROM bestellungen GROUP BY artikel_id, plz")
    bestellungen_raw = cur.fetchall()

    matrix = {}
    for row in bestellungen_raw:
        aid = row['artikel_id']
        if aid not in matrix:
            matrix[aid] = {}
        matrix[aid][row['plz']] = row['summe']

    artikel_liste = []
    for art in artikel_raw:
        artikel_liste.append({
            "name": art["name"],
            "lieferant": art["lieferant"],
            "tag": art["tag"],
            "bestellungen": matrix.get(art["id"], {})
        })

    if format == "csv":
        import io, csv
        from flask import make_response
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Artikel", *[f["plz"] for f in filialen]])
        for art in artikel_liste:
            row = [f"{art['name']} ({art['lieferant']} / {art['tag']})"]
            row += [art["bestellungen"].get(f["plz"], 0) for f in filialen]
            writer.writerow(row)
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=bestellungen.csv"
        response.headers["Content-type"] = "text/csv"
        return response

    if format == "xlsx":
        import io
        import xlsxwriter
        from flask import make_response
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': True})
        worksheet.write(0, 0, "Artikel", bold)
        for idx, f in enumerate(filialen):
            worksheet.write(0, idx + 1, f["plz"], bold)
        for r, art in enumerate(artikel_liste, 1):
            worksheet.write(r, 0, f"{art['name']} ({art['lieferant']} / {art['tag']})")
            for c, f in enumerate(filialen):
                worksheet.write(r, c + 1, art["bestellungen"].get(f["plz"], 0))
        workbook.close()
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=bestellungen.xlsx"
        response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return response

    if format == "pdf":
            from fpdf import FPDF
            from flask import make_response

            class PDF(FPDF):
                def header(self):
                    self.set_font("Courier", "B", 14)
                    self.cell(0, 10, "SmartSupply - Bestellungen (Matrix)", ln=True, align="C")
                    self.ln(4)

            pdf = PDF(orientation='L', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=True, margin=10)
            pdf.add_page()
            pdf.set_font("Helvetica", size=9)

            # Spaltenbreite dynamisch berechnen
            artikel_width = 100
            filial_width = (277 - artikel_width) / len(filialen)

            # Kopfzeile
            pdf.set_font("Arial", "B", 9)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(artikel_width, 8, "Artikel", border=1, fill=True)
            for f in filialen:
                pdf.cell(filial_width, 8, f["plz"], border=1, fill=True)
            pdf.ln()

            # Inhalt
            pdf.set_font("Arial", "", 8)
            for art in artikel_liste:
                artikel_text = f"{art['name']} ({art['lieferant']}, {art['tag']})"
                if len(artikel_text) > 60:
                    artikel_text = artikel_text[:57] + "..."

                pdf.cell(artikel_width, 8, artikel_text, border=1)
                for f in filialen:
                    menge = str(art["bestellungen"].get(f["plz"], 0))
                    pdf.cell(filial_width, 8, menge, border=1, align="C")
                pdf.ln()

            response = make_response(pdf.output(dest='S').encode('latin-1', 'replace'))
            response.headers["Content-Disposition"] = "attachment; filename=bestellungen.pdf"
            response.headers["Content-type"] = "application/pdf"
            return response


if __name__ == '__main__':
    app.run(debug=True)