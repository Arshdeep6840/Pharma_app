from app import connect_db

def insert_sample_data():
    conn = connect_db()
    cur = conn.cursor()

    # ---------------- USERS ----------------
    users_data = [
        ("admin", "admin", "admin"),
        ("pharma", "123", "pharmacist"),
        ("staff1", "123", "staff")
    ]

    cur.executemany(
        "INSERT INTO users(username,password,role) VALUES(?,?,?)",
        users_data
    )

    # ---------------- MEDICINES ----------------
    medicines_data = [
        ("Paracetamol", "Cipla", 20, 50, "2026-05-10"),
        ("Aspirin", "Sun Pharma", 15, 8, "2026-04-01"),
        ("Ibuprofen", "Dr Reddy", 30, 5, "2026-03-25"),
        ("Amoxicillin", "Mankind", 45, 25, "2026-06-15"),
        ("Cetirizine", "Zydus", 10, 12, "2026-03-28"),
        ("Dolo 650", "Micro Labs", 25, 60, "2026-07-20"),
        ("Azithromycin", "Cipla", 70, 3, "2026-03-22")
    ]

    cur.executemany(
        "INSERT INTO medicine(name, company, price, quantity, expiry) VALUES(?,?,?,?,?)",
        medicines_data
    )

    conn.commit()
    conn.close()

insert_sample_data()