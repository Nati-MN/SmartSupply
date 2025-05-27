from flask import Blueprint, render_template, session, redirect, make_response
from datetime import datetime
import io
import csv
import xlsxwriter
from fpdf import FPDF
from db import get_db, get_filialname


admin = Blueprint('admin', __name__)

@admin.route('/admin')
def admin_dashboard():
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

@admin.route('/admin_matrix')
def admin_matrix():
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
            "id": art["id"],
            "name": art["name"],
            "lieferant": art["lieferant"],
            "tag": art["tag"],
            "bestellungen": matrix.get(art["id"], {})
        })

    return render_template("admin_matrix.html", artikel_liste=artikel_liste, filialen=filialen, current_date=datetime.today().strftime('%d.%m.%Y'))

@admin.route('/admin_matrix_export/<format>')
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
        class PDF(FPDF):
            def header(self):
                self.set_font("Courier", "B", 14)
                self.cell(0, 10, "SmartSupply - Bestellungen (Matrix)", ln=True, align="C")
                self.ln(4)

        pdf = PDF(orientation='L', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=10)
        pdf.add_page()
        pdf.set_font("Helvetica", size=9)

        artikel_width = 100
        filial_width = (277 - artikel_width) / len(filialen)

        pdf.set_font("Arial", "B", 9)
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(artikel_width, 8, "Artikel", border=1, fill=True)
        for f in filialen:
            pdf.cell(filial_width, 8, f["plz"], border=1, fill=True)
        pdf.ln()

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