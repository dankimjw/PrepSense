"""Service functions for accessing pantry data in the database."""

from database import get_db

class PantryService:
    def __init__(self):
        """
        Initializes the PantryService with a database connection.
        """
        self.db = get_db()

    def get_pantry_items(self):
        """
        Retrieves all pantry items from the database.
        """
        return self.db.execute("SELECT * FROM pantry_items").fetchall()

    def add_pantry_item(self, item):
        """
        Adds a new pantry item to the database.
        """
        self.db.execute(
            "INSERT INTO pantry_items (name, quantity, expiration_date) VALUES (?, ?, ?)",
            (item["name"], item["quantity"], item["expiration_date"])
        )
        self.db.commit()
        return {"message": "Item added successfully"}