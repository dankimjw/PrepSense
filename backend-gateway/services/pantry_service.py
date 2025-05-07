from database import get_db

def get_pantry_items():
    db = get_db()
    return db.execute("SELECT * FROM pantry_items").fetchall()

def add_pantry_item(item):
    db = get_db()
    db.execute("INSERT INTO pantry_items (name, quantity, expiration_date) VALUES (?, ?, ?)",
               (item["name"], item["quantity"], item["expiration_date"]))
    db.commit()
    return {"message": "Item added successfully"}