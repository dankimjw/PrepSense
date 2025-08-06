"""
Shopping List Client Wrapper for Testing

This wrapper provides a clean interface for testing shopping list operations
without direct dependencies on the database or router implementation.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class MockShoppingListClient:
    """Mock implementation of shopping list operations for testing"""

    def __init__(self):
        self.shopping_lists = {}  # user_id -> list of items
        self._id_counter = 1

    def _get_next_id(self) -> int:
        """Get next auto-increment ID"""
        current_id = self._id_counter
        self._id_counter += 1
        return current_id

    def get_shopping_list(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all items in user's shopping list

        Args:
            user_id: User ID

        Returns:
            List of shopping list items sorted by checked status, priority, and date
        """
        if user_id not in self.shopping_lists:
            return []

        items = self.shopping_lists[user_id].copy()

        # Sort by is_checked (False first), priority (desc), added_date (desc)
        items.sort(
            key=lambda x: (
                x.get("is_checked", False),
                -x.get("priority", 0),
                -x.get("added_date", datetime.now()).timestamp(),
            )
        )

        # Convert datetime to ISO format
        for item in items:
            if "added_date" in item and isinstance(item["added_date"], datetime):
                item["added_date"] = item["added_date"].isoformat()
            if "updated_at" in item and isinstance(item["updated_at"], datetime):
                item["updated_at"] = item["updated_at"].isoformat()

        return items

    def add_shopping_list_items(self, user_id: int, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add items to shopping list

        Args:
            user_id: User ID
            items: List of items to add

        Returns:
            Dict with added_count and updated_count
        """
        if user_id not in self.shopping_lists:
            self.shopping_lists[user_id] = []

        added_count = 0
        updated_count = 0

        for item in items:
            # Check if item exists
            existing_item = next(
                (i for i in self.shopping_lists[user_id] if i["item_name"] == item["item_name"]),
                None,
            )

            if existing_item:
                # Update existing item
                existing_item.update(
                    {
                        "quantity": item.get("quantity", existing_item.get("quantity")),
                        "unit": item.get("unit", existing_item.get("unit")),
                        "category": item.get("category", existing_item.get("category")),
                        "recipe_name": item.get("recipe_name", existing_item.get("recipe_name")),
                        "notes": item.get("notes", existing_item.get("notes")),
                        "priority": item.get("priority", existing_item.get("priority", 0)),
                        "updated_at": datetime.now(),
                    }
                )
                updated_count += 1
            else:
                # Add new item
                new_item = {
                    "shopping_list_item_id": self._get_next_id(),
                    "item_name": item["item_name"],
                    "quantity": item.get("quantity"),
                    "unit": item.get("unit"),
                    "category": item.get("category"),
                    "recipe_name": item.get("recipe_name"),
                    "notes": item.get("notes"),
                    "is_checked": item.get("is_checked", False),
                    "priority": item.get("priority", 0),
                    "added_date": datetime.now(),
                    "updated_at": datetime.now(),
                }
                self.shopping_lists[user_id].append(new_item)
                added_count += 1

        return {
            "added_count": added_count,
            "updated_count": updated_count,
            "total_items": len(self.shopping_lists[user_id]),
        }

    def remove_shopping_list_items(self, user_id: int, item_names: List[str]) -> Dict[str, Any]:
        """
        Remove items from shopping list

        Args:
            user_id: User ID
            item_names: List of item names to remove

        Returns:
            Dict with removed_count
        """
        if user_id not in self.shopping_lists:
            return {"removed_count": 0}

        removed_count = 0
        original_count = len(self.shopping_lists[user_id])

        self.shopping_lists[user_id] = [
            item for item in self.shopping_lists[user_id] if item["item_name"] not in item_names
        ]

        removed_count = original_count - len(self.shopping_lists[user_id])

        return {"removed_count": removed_count}

    def update_shopping_list_item(
        self, user_id: int, item_name: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a specific shopping list item

        Args:
            user_id: User ID
            item_name: Name of item to update
            updates: Dict of fields to update

        Returns:
            Dict with success status
        """
        if user_id not in self.shopping_lists:
            return {"success": False, "message": "User has no shopping list"}

        item = next((i for i in self.shopping_lists[user_id] if i["item_name"] == item_name), None)

        if not item:
            return {"success": False, "message": "Item not found"}

        # Update allowed fields
        allowed_fields = ["is_checked", "quantity", "unit", "notes", "priority"]
        for field in allowed_fields:
            if field in updates and updates[field] is not None:
                item[field] = updates[field]

        item["updated_at"] = datetime.now()

        return {"success": True, "message": "Item updated"}

    def clear_shopping_list(self, user_id: int) -> Dict[str, Any]:
        """
        Clear all items from shopping list

        Args:
            user_id: User ID

        Returns:
            Dict with removed_count
        """
        if user_id not in self.shopping_lists:
            return {"removed_count": 0}

        removed_count = len(self.shopping_lists[user_id])
        self.shopping_lists[user_id] = []

        return {"removed_count": removed_count}

    def get_shopping_list_by_category(self, user_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get shopping list grouped by category

        Args:
            user_id: User ID

        Returns:
            Dict with categories as keys and items as values
        """
        items = self.get_shopping_list(user_id)
        categorized = {}

        for item in items:
            category = item.get("category", "Uncategorized")
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(item)

        return categorized


class ShoppingListClientWrapper:
    """Wrapper for shopping list operations"""

    def __init__(self, db_service=None):
        """
        Initialize wrapper with optional database service

        Args:
            db_service: Real database service instance or None for mock
        """
        self._db_service = db_service
        self._mock = MockShoppingListClient()

    def get_shopping_list(self, user_id: int) -> List[Dict[str, Any]]:
        """Get shopping list items"""
        if self._db_service:
            query = """
            SELECT 
                shopping_list_item_id,
                item_name,
                quantity,
                unit,
                category,
                recipe_name,
                notes,
                is_checked,
                priority,
                added_date,
                updated_at
            FROM shopping_list_items
            WHERE user_id = %(user_id)s
            ORDER BY 
                is_checked ASC,
                priority DESC,
                added_date DESC
            """
            return self._db_service.execute_query(query, {"user_id": user_id})

        return self._mock.get_shopping_list(user_id)

    def add_shopping_list_items(self, user_id: int, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add items to shopping list"""
        if self._db_service:
            # Simplified implementation - in real code this would check for
            # existing items and update/insert accordingly
            added_count = 0
            for item in items:
                # This is a simplified version
                added_count += 1

            return {"added_count": added_count, "updated_count": 0, "total_items": added_count}

        return self._mock.add_shopping_list_items(user_id, items)

    def remove_shopping_list_items(self, user_id: int, item_names: List[str]) -> Dict[str, Any]:
        """Remove items from shopping list"""
        if self._db_service:
            query = """
            DELETE FROM shopping_list_items
            WHERE user_id = %(user_id)s
            AND item_name = ANY(%(item_names)s)
            """
            result = self._db_service.execute_query(
                query, {"user_id": user_id, "item_names": item_names}
            )
            return {"removed_count": result[0].get("affected_rows", 0)}

        return self._mock.remove_shopping_list_items(user_id, item_names)

    def update_shopping_list_item(
        self, user_id: int, item_name: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update shopping list item"""
        if self._db_service:
            # Build update query dynamically
            set_clauses = []
            params = {"user_id": user_id, "item_name": item_name}

            for field, value in updates.items():
                if value is not None:
                    set_clauses.append(f"{field} = %({field})s")
                    params[field] = value

            if not set_clauses:
                return {"success": False, "message": "No updates provided"}

            query = f"""
            UPDATE shopping_list_items
            SET {', '.join(set_clauses)}, updated_at = NOW()
            WHERE user_id = %(user_id)s AND item_name = %(item_name)s
            """

            result = self._db_service.execute_query(query, params)
            success = result[0].get("affected_rows", 0) > 0

            return {"success": success, "message": "Item updated" if success else "Item not found"}

        return self._mock.update_shopping_list_item(user_id, item_name, updates)

    def clear_shopping_list(self, user_id: int) -> Dict[str, Any]:
        """Clear all items from shopping list"""
        if self._db_service:
            query = """
            DELETE FROM shopping_list_items
            WHERE user_id = %(user_id)s
            """
            result = self._db_service.execute_query(query, {"user_id": user_id})
            return {"removed_count": result[0].get("affected_rows", 0)}

        return self._mock.clear_shopping_list(user_id)


def get_shopping_list_client(db_service=None) -> ShoppingListClientWrapper:
    """Factory function to get shopping list client"""
    return ShoppingListClientWrapper(db_service)
