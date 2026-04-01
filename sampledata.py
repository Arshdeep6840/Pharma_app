from app import connect_db
def insert_sample_data():
    conn = connect_db()
    cur = conn.cursor()

    # sample_data = [
    #     ("Paracetamol", "Cipla", 20, 50, "2026-05-10"),
    #     ("Aspirin", "Sun Pharma", 15, 8, "2026-04-01"),
    #     ("Ibuprofen", "Dr Reddy", 30, 5, "2026-03-25"),
    #     ("Amoxicillin", "Mankind", 45, 25, "2026-06-15"),
    #     ("Cetirizine", "Zydus", 10, 12, "2026-03-28"),
    #     ("Dolo 650", "Micro Labs", 25, 60, "2026-07-20"),
    #     ("Azithromycin", "Cipla", 70, 3, "2026-03-22")
    # ]

    # cur.executemany(
    #     "INSERT INTO medicine(name, company, price, quantity, expiry) VALUES(?,?,?,?,?)",
    #     sample_data
    # )
    cur.executemany(
        # "INSERT INTO medicine(name, company, price, quantity, expiry) VALUES(?,?,?,?,?)",
        # sample_data
        "INSERT INTO users(username,password,role) VALUES('admin','admin','admin');"
    )
    conn.commit()
    conn.close()
insert_sample_data()