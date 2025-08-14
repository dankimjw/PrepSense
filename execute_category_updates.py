#!/usr/bin/env python3
"""
Execute the category updates using the existing PostgreSQL connection.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables  
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend_gateway'))

from backend_gateway.config.database import get_database_service


# All the update statements
UPDATE_STATEMENTS = [
    "UPDATE pantry_items SET category = 'Condiments' WHERE pantry_item_id = 492564739; -- Guacamole",
    "UPDATE pantry_items SET category = 'Spices' WHERE pantry_item_id = 491386731; -- Salt", 
    "UPDATE pantry_items SET category = 'Condiments' WHERE pantry_item_id = 311652453; -- Chopped Chipotle Chiles In Adobo",
    "UPDATE pantry_items SET category = 'Condiments' WHERE pantry_item_id = 310483427; -- Fat Free Mayonnaise",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 183183272; -- finely diced celery",
    "UPDATE pantry_items SET category = 'Fresh Herbs' WHERE pantry_item_id = 180848327; -- fresh chopped parsley",
    "UPDATE pantry_items SET category = 'Spices' WHERE pantry_item_id = 177017660; -- Ground Black Pepper",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 175685741; -- Green Bell Pepper",
    "UPDATE pantry_items SET category = 'Spices' WHERE pantry_item_id = 173370849; -- Garlic Powder",
    "UPDATE pantry_items SET category = 'Dairy' WHERE pantry_item_id = 171111536; -- Greek Yogurt",
    "UPDATE pantry_items SET category = 'Dairy' WHERE pantry_item_id = 283913515; -- Eggs",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 275632632; -- Bell Peppers",
    "UPDATE pantry_items SET category = 'Condiments' WHERE pantry_item_id = 271568796; -- Olive Oil",
    "UPDATE pantry_items SET category = 'Pantry Staples' WHERE pantry_item_id = 267359879; -- Pasta",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 263311925; -- Tomatoes",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 258950930; -- Garlic",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 254585279; -- Onions",
    "UPDATE pantry_items SET category = 'Rice & Grains' WHERE pantry_item_id = 250583445; -- Rice",
    "UPDATE pantry_items SET category = 'Meat & Poultry' WHERE pantry_item_id = 246396475; -- Chicken Breast",
    "UPDATE pantry_items SET category = 'Bakery & Pastries' WHERE pantry_item_id = 955147328; -- whole grain sandwich thins",
    "UPDATE pantry_items SET category = 'Condiments' WHERE pantry_item_id = 953990210; -- 1/2- 2 Tbsp pesto",
    "UPDATE pantry_items SET category = 'Bakery & Pastries' WHERE pantry_item_id = 950106247; -- Wheat Hamburger Buns",
    "UPDATE pantry_items SET category = 'Dairy' WHERE pantry_item_id = 948969307; -- Wedges Laughing Cow Swiss Cheese",
    "UPDATE pantry_items SET category = 'Meat & Poultry' WHERE pantry_item_id = 947816642; -- slices Turkey Bacon",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 946753640; -- Onion, Sliced Into Strips",
    "UPDATE pantry_items SET category = 'Condiments' WHERE pantry_item_id = 945600655; -- Lime Juice",
    "UPDATE pantry_items SET category = 'Spices' WHERE pantry_item_id = 944529485; -- Ground Cumin",
    "UPDATE pantry_items SET category = 'Snacks & Treats' WHERE pantry_item_id = 361171556; -- Dark Chocolate",
    "UPDATE pantry_items SET category = 'Dairy' WHERE pantry_item_id = 360014477; -- Milk",
    "UPDATE pantry_items SET category = 'Dairy' WHERE pantry_item_id = 358890441; -- Paneer",
    "UPDATE pantry_items SET category = 'Meat & Poultry' WHERE pantry_item_id = 357776320; -- Chicken Breast",
    "UPDATE pantry_items SET category = 'Dairy' WHERE pantry_item_id = 356573547; -- Greek Yogurt",
    "UPDATE pantry_items SET category = 'Dairy' WHERE pantry_item_id = 355459911; -- Eggs",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 351682105; -- Orange Bell Pepper",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 350555081; -- Raspberries",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 349454457; -- Strawberries",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 348374102; -- Poblano Pepper",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 347281181; -- Yellow Bell Pepper",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 346160403; -- Cremini Mushrooms",
    "UPDATE pantry_items SET category = 'Snacks & Treats' WHERE pantry_item_id = 41845494; -- Walnuts",
    "UPDATE pantry_items SET category = 'Rice & Grains' WHERE pantry_item_id = 38016213; -- Oats",
    "UPDATE pantry_items SET category = 'Condiments' WHERE pantry_item_id = 34189691; -- Honey",
    "UPDATE pantry_items SET category = 'Dairy' WHERE pantry_item_id = 30846782; -- Greek Yogurt",
    "UPDATE pantry_items SET category = 'Dairy' WHERE pantry_item_id = 27292389; -- Almond Milk",
    "UPDATE pantry_items SET category = 'Snacks & Treats' WHERE pantry_item_id = 23793723; -- Chia Seeds",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 20088796; -- Avocados",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 16526394; -- Kale",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 12729391; -- Sweet Potatoes",
    "UPDATE pantry_items SET category = 'Rice & Grains' WHERE pantry_item_id = 9007149; -- Quinoa",
    "UPDATE pantry_items SET category = 'Condiments' WHERE pantry_item_id = 955663916; -- Sun Dried Tomatoes",
    "UPDATE pantry_items SET category = 'Snacks & Treats' WHERE pantry_item_id = 952228883; -- Pine Nuts",
    "UPDATE pantry_items SET category = 'Condiments' WHERE pantry_item_id = 948697370; -- Balsamic Vinegar",
    "UPDATE pantry_items SET category = 'Fresh Herbs' WHERE pantry_item_id = 941074668; -- Basil",
    "UPDATE pantry_items SET category = 'Pantry Staples' WHERE pantry_item_id = 937665794; -- Pasta",
    "UPDATE pantry_items SET category = 'Dairy' WHERE pantry_item_id = 930180177; -- Parmesan Cheese",
    "UPDATE pantry_items SET category = 'Condiments' WHERE pantry_item_id = 863484224; -- Fish Sauce",
    "UPDATE pantry_items SET category = 'Dairy' WHERE pantry_item_id = 853442955; -- Coconut Milk",
    "UPDATE pantry_items SET category = 'Rice & Grains' WHERE pantry_item_id = 849767276; -- Jasmine Rice",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 845514818; -- Mushrooms",
    "UPDATE pantry_items SET category = 'Condiments' WHERE pantry_item_id = 828186501; -- Sesame Oil",
    "UPDATE pantry_items SET category = 'Condiments' WHERE pantry_item_id = 823162614; -- Soy Sauce",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 754427996; -- Bell Pepper",
    "UPDATE pantry_items SET category = 'Spices' WHERE pantry_item_id = 746031035; -- Chili Powder",
    "UPDATE pantry_items SET category = 'Spices' WHERE pantry_item_id = 737133528; -- Cumin",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 732852446; -- Diced Tomatoes",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 729063710; -- Garlic",
    "UPDATE pantry_items SET category = 'Meat & Poultry' WHERE pantry_item_id = 721923590; -- Ground Beef",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 439850627; -- Strawberries",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 436088676; -- Raspberries",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 748662749; -- Strawberries",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 746536532; -- Raspberries",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 466292704; -- Raspberries",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 464049177; -- Strawberries",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 208726895; -- strawberries",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 935606102; -- Whole Strawberries",
    "UPDATE pantry_items SET category = 'Fresh Produce' WHERE pantry_item_id = 771787809; -- Whole Strawberries"
]


async def main():
    """Execute all category updates."""
    
    try:
        # Get database service
        db_service = get_database_service()
        
        print(f"Executing {len(UPDATE_STATEMENTS)} category updates...")
        
        updated_count = 0
        failed_count = 0
        
        for i, statement in enumerate(UPDATE_STATEMENTS, 1):
            try:
                # Extract the comment for better logging
                parts = statement.split(' -- ')
                item_name = parts[1] if len(parts) > 1 else f"item {i}"
                
                # Execute the update (remove the comment part)
                sql = parts[0]
                result = db_service.execute_query(sql)
                
                updated_count += 1
                print(f"  ✅ {i}/{len(UPDATE_STATEMENTS)}: Updated {item_name}")
                
            except Exception as e:
                failed_count += 1
                print(f"  ❌ {i}/{len(UPDATE_STATEMENTS)}: Failed to update {item_name}: {e}")
        
        print(f"\\n🎉 Category update complete!")
        print(f"  ✅ Successfully updated: {updated_count} items")
        print(f"  ❌ Failed to update: {failed_count} items")
        
        if updated_count > 0:
            print("\\n📊 Verifying updates...")
            
            # Check the new category distribution
            verify_query = """
            SELECT pi.category, COUNT(*) as count
            FROM pantry_items pi
            JOIN pantries p ON pi.pantry_id = p.pantry_id
            JOIN users u ON p.user_id = u.user_id
            WHERE u.user_id = 111
            GROUP BY pi.category
            ORDER BY pi.category;
            """
            
            categories = db_service.execute_query(verify_query)
            print("\\nUpdated category distribution:")
            for cat in categories:
                print(f"  {cat['category']}: {cat['count']} items")
        
        return 0 if failed_count == 0 else 1
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))