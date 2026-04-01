from flask import Flask, render_template, request, redirect, session, jsonify,send_file
import sqlite3, json
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DB ----------------
def connect_db():
    return sqlite3.connect("database.db")
def create_table():
    conn = connect_db()
    cur = conn.cursor()

    # USERS
    cur.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        role TEXT
    )''')

    # MEDICINE
    cur.execute('''CREATE TABLE IF NOT EXISTS medicine(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        company TEXT,
        price REAL,
        quantity INTEGER,
        expiry TEXT,
        batch TEXT
    )''')

    # SUPPLIER
    cur.execute('''CREATE TABLE IF NOT EXISTS supplier(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        contact TEXT
    )''')

    # SALES
    cur.execute('''CREATE TABLE IF NOT EXISTS sales(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_name TEXT,
        quantity INTEGER,
        total_price REAL,
        date TEXT
    )''')
    cur.execute("INSERT INTO users(username,password,role) VALUES('admin','admin','admin');")

    conn.commit()
    conn.close()
create_table()

# ---------------- AUTH ----------------
def is_logged_in():
    return "user" in session

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user,pwd))
        data = cur.fetchone()

        if data:
            session["user"]=user
            return redirect("/dashboard")

    return render_template("login.html")


import pandas as pd
from sklearn.linear_model import LinearRegression

def predict_demand():
    conn = connect_db()
    df = pd.read_sql_query("SELECT * FROM sales", conn)

    df['day'] = pd.to_datetime(df['date']).dt.day
    X = df[['day']]
    y = df['quantity']

    model = LinearRegression()
    model.fit(X, y)

    future = [[31]]
    pred = model.predict(future)

    return int(pred[0])
# ---------------- DASHBOARD ----------------
from datetime import datetime, timedelta
@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect("/")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT name, quantity, expiry FROM medicine")
    data = cur.fetchall()

    names = []
    qty = []
    exp_labels = []
    exp_days = []

    today = datetime.today()

    expiring_soon = []
    expired = []
    cur.execute("SELECT medicine_name, SUM(quantity) FROM sales GROUP BY medicine_name")
    top = cur.fetchall()

    top_names = [i[0] for i in top]
    top_qty = [i[1] for i in top]
    top_names=json.dumps(top_names),
    top_qty=json.dumps(top_qty)
    for name, quantity, expiry in data:
        names.append(name)
        qty.append(quantity)

        exp_date = datetime.strptime(expiry, "%Y-%m-%d")
        days_left = (exp_date - today).days

        exp_labels.append(name)
        exp_days.append(days_left)

        if days_left < 0:
            expired.append((name, days_left))
        elif days_left <= 30:
            expiring_soon.append((name, days_left))

    # ✅ ADD THESE
    total = len(data)
    low_stock = len([i for i in data if i[1] < 10])
    expiring = len(expiring_soon)

    return render_template("dashboard.html",
                           names=json.dumps(names),
                           qty=json.dumps(qty),
                           exp_labels=json.dumps(exp_labels),
                           exp_days=json.dumps(exp_days),
                           expiring_soon=expiring_soon,
                           expired=expired,
                           total=total,
                           low_stock=low_stock,
                           expiring=expiring,
                           top_names = top_names,
                           top_qty=top_qty,
                           prediction = predict_demand())
# ---------------- ADD ----------------
@app.route("/add", methods=["GET", "POST"])
def add():
    if not is_logged_in():
        return redirect("/")

    if request.method == "POST":
        conn = connect_db()
        cur = conn.cursor()

        cur.execute("INSERT INTO medicine(name,company,price,quantity,expiry) VALUES(?,?,?,?,?)",
                    (request.form["name"],
                     request.form["company"],
                     request.form["price"],
                     request.form["quantity"],
                     request.form["expiry"]))

        conn.commit()
        return redirect("/view")

    return render_template("add.html")

# ---------------- VIEW + SEARCH ----------------
@app.route("/view")
def view():
    if not is_logged_in():
        return redirect("/")

    search = request.args.get("search", "")

    conn = connect_db()
    cur = conn.cursor()

    if search:
        cur.execute("SELECT * FROM medicine WHERE name LIKE ?", ('%' + search + '%',))
    else:
        cur.execute("SELECT * FROM medicine")

    data = cur.fetchall()

    return render_template("view.html", data=data, search=search)

# ---------------- UPDATE ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if not is_logged_in():
        return redirect("/")

    conn = connect_db()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("""UPDATE medicine 
                       SET name=?, company=?, price=?, quantity=?, expiry=? 
                       WHERE id=?""",
                    (request.form["name"],
                     request.form["company"],
                     request.form["price"],
                     request.form["quantity"],
                     request.form["expiry"],
                     id))
        conn.commit()
        return redirect("/view")

    cur.execute("SELECT * FROM medicine WHERE id=?", (id,))
    data = cur.fetchone()

    return render_template("edit.html", data=data)

# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):
    if not is_logged_in():
        return redirect("/")

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM medicine WHERE id=?", (id,))
    conn.commit()

    return redirect("/view")

# ---------------- API (LOW STOCK) ----------------
@app.route("/api/low-stock")
def low_stock_api():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT name, quantity FROM medicine WHERE quantity < 10")
    data = cur.fetchall()

    return jsonify(data)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
@app.route("/sale", methods=["GET","POST"])
def sale():
    if not is_logged_in():
        return redirect("/")

    conn = connect_db()
    cur = conn.cursor()

    if request.method == "POST":
        items = request.form.getlist("name")
        qtys = request.form.getlist("qty")

        total_bill = 0
        last_sale_id = None

        for i in range(len(items)):
            name = items[i]
            qty = int(qtys[i])

            cur.execute("SELECT price, quantity FROM medicine WHERE name=?", (name,))
            med = cur.fetchone()

            if med:
                price, stock = med

                if stock >= qty:
                    total = price * qty
                    total_bill += total

                    cur.execute(
                        "INSERT INTO sales(medicine_name, quantity, total_price, date) VALUES(?,?,?,?)",
                        (name, qty, total, datetime.now().strftime("%Y-%m-%d"))
                    )

                    last_sale_id = cur.lastrowid

                    cur.execute(
                        "UPDATE medicine SET quantity = quantity - ? WHERE name=?",
                        (qty, name)
                    )
                else:
                    return "❌ Sale failed! Check stock or input."

        conn.commit()
        conn.close()

        # ✅ Redirect to invoice automatically
        return redirect(f"/invoice/{last_sale_id}")

    cur.execute("SELECT name FROM medicine")
    meds = cur.fetchall()
    conn.close()

    return render_template("sale.html", meds=meds)
@app.route("/sales-report")
def sales_report():
    if not is_logged_in():
        return redirect("/")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM sales")
    data = cur.fetchall()

    # Revenue chart
    cur.execute("SELECT date, SUM(total_price) FROM sales GROUP BY date")
    chart = cur.fetchall()

    dates = [i[0] for i in chart]
    revenue = [i[1] for i in chart]

    total_revenue = sum(revenue)

    return render_template("sales.html",
                           data=data,
                           dates=json.dumps(dates),
                           revenue=json.dumps(revenue),
                           total_revenue=total_revenue)
    
    
    

@app.route("/invoice/<int:id>")
def invoice(id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM sales WHERE id=?", (id,))
    data = cur.fetchone()
    conn.close()

    file = f"invoice_{id}.pdf"

    doc = SimpleDocTemplate(file, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []

    # 🏥 TITLE
    elements.append(Paragraph("<b>Pharmacy Management System</b>", styles['Title']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>Invoice</b>", styles['Heading2']))
    elements.append(Spacer(1, 10))

    # 📅 INFO
    elements.append(Paragraph(f"Invoice ID: {data[0]}", styles['Normal']))
    elements.append(Paragraph(f"Date: {data[4]}", styles['Normal']))
    elements.append(Spacer(1, 15))

    # 📊 TABLE DATA
    table_data = [
        ["Medicine", "Quantity", "Price (₹)", "Total (₹)"],
        [data[1], data[2], f"{data[3]/data[2]:.2f}", f"{data[3]:.2f}"]
    ]

    table = Table(table_data, colWidths=[150, 80, 100, 100])

    # 🎨 TABLE STYLE
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),

        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # 💰 TOTAL
    elements.append(Paragraph(f"<b>Grand Total: ₹{data[3]:.2f}</b>", styles['Heading3']))
    elements.append(Spacer(1, 20))

    # 🙏 FOOTER
    elements.append(Paragraph("Thank you for your purchase!", styles['Normal']))

    doc.build(elements)

    return send_file(file, as_attachment=True)
# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
    
    
