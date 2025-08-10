"""Service wrapper around OpenAI's vision API."""

# File: PrepSense/backend_gateway/services/vision_service.py
import base64
import json
import re
from datetime import datetime, timedelta
from typing import Any, Optional

from dotenv import load_dotenv

from backend_gateway.core.openai_client import get_openai_client

# Load environment variables.
load_dotenv()

# --- Ensure your OpenAI client initialization is correct for your library version ---
# For older library versions (pre v1.0.0):
# openai.api_key = os.getenv("OPENAI_API_KEY")
# client = openai # Not strictly needed if calling openai.ChatCompletion directly

# For newer library versions (v1.0.0+):
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Make sure this matches how you instantiate/use it in classify_food_items


class VisionService:
    def __init__(self):
        """
        Initializes the VisionService with an OpenAI client.
        """
        try:
            self.client = get_openai_client()
        except ValueError as e:
            raise ValueError(f"Failed to initialize VisionService: {e}") from e

    async def process_image(self, file) -> tuple[str, Optional[str]]:
        """
        Reads and preprocesses the uploaded image file.
        Converts the image to base64 format for OpenAI API.
        Returns a tuple of (base64_image, content_type).
        """
        img_bytes = await file.read()
        base64_image = base64.b64encode(img_bytes).decode("utf-8")
        return base64_image, file.content_type

    def classify_food_items(self, base64_image: str, content_type: Optional[str]) -> str:
        """
        Sends the base64-encoded image to OpenAI's API with a detailed prompt.
        Returns the raw JSON response string from OpenAI.
        """
        today_str = datetime.today().strftime("%Y-%m-%d")
        prompt_text = (
            f"You are a grocery inventory assistant helping track food items.\n\n"
            f"Today's date is {today_str}.\n\n"
            "Instructions:\n"
            "- Carefully examine the image for any visible food products.\n"
            "- For each item identified, follow this detailed reasoning:\n"
            "  1. Read all visible text and branding on the packaging to identify the full item name.\n"
            "     - Include brand and type (e.g., 'Oasis Orange Juice', 'Great Value Basmati Rice').\n"
            "  2. Scan the package for quantity indicators and use appropriate units based on category:\n"
            "     - PRODUCE (fruits/vegetables): Use 'lb', 'oz', 'each', 'bunch', 'head', 'container', 'bag' (NOT ml, L, fl oz)\n"
            "       Examples: '2 lb strawberries', '1 head lettuce', '3 each apples'\n"
            "     - DAIRY: Liquid dairy use 'gallon', 'quart', 'pint', 'fl oz'; Solid dairy use 'oz', 'lb', 'slice'; Eggs use 'dozen' or 'each'\n"
            "       Examples: '1 gallon milk', '8 oz cheese', '1 dozen eggs'\n"
            "     - MEAT/SEAFOOD: Use 'lb', 'oz', 'piece', 'package' (NOT ml, L, each)\n"
            "       Examples: '1.5 lb ground beef', '4 piece chicken breast'\n"
            "     - BEVERAGES: Use 'bottle', 'can', 'gallon', 'liter', 'fl oz' (NOT lb, oz, each)\n"
            "       Examples: '2 liter soda', '12 can beer', '64 fl oz juice'\n"
            "     - BAKERY/GRAINS: Use 'loaf', 'each', 'lb', 'oz', 'package'\n"
            "       Examples: '1 loaf bread', '2 lb rice', '16 oz pasta'\n"
            "     - CANNED GOODS: Use 'can', 'oz', 'jar' \n"
            "       Examples: '15 oz can beans', '24 oz jar sauce'\n"
            "     - SPICES: Use 'oz', 'container', 'jar' (NOT lb, gallon)\n"
            "       Examples: '2 oz pepper', '1 jar oregano'\n"
            "  3. Item Count Details:\n"
            "     - For each distinct food item type identified, carefully count all visible units of that exact item in the image.\n"
            "     - This total visual count should be an integer, and you must include it in the 'count' field for that item's JSON object.\n"
            "     - For example, if there are 5 identical cans of 'Joe's O's Cereal' visible, the 'count' field for that item's entry must be 5.\n"
            "     - Please ensure the 'count' field is always present in each item's JSON object.\n"
            "  4. Classify each item into the most appropriate category from this list:\n"
            "     - Dairy: Milk, cheese, yogurt, butter, cream\n"
            "     - Meat: Fresh meat, poultry, processed meats\n"
            "     - Produce: Fresh fruits, vegetables, herbs\n"
            "     - Bakery: Bread, pastries, baked goods\n"
            "     - Pantry: Rice, pasta, flour, spices, oil, condiments\n"
            "     - Beverages: Juices, sodas, water, coffee, tea\n"
            "     - Frozen: Frozen foods, ice cream\n"
            "     - Snacks: Chips, crackers, candy, nuts\n"
            "     - Canned Goods: Canned vegetables, fruits, soups\n"
            "     - Deli: Prepared foods, sandwich meats\n"
            "     - Seafood: Fish, shellfish, seafood products\n"
            "     - Other: Items that don't fit other categories\n"
            "  5. Look for any printed expiration date.\n"
            "     - Accept 'Best Before', 'Use By', 'BB', or 'Expiry'.\n"
            "     - If no printed date, estimate based on type:\n"
            "         - Green banana: +7 days\n"
            "         - Yellow banana: +5 days\n"
            "         - Black banana: +2 days\n"
            "         - Milk: +7 days\n"
            "         - Yogurt: +10 days\n"
            "         - Jarred sauces: +180 days\n"
            "         - Staples (rice, oats, sugar, flour, lentils): +365 days\n"
            "- Do not assign a date earlier than today's date.\n\n"
            "Format your answer as a STRICT JSON array ONLY like this:\n"
            "[\n"
            '  {"item_name": <string>, "quantity": <string>, "count": <integer>, "category": <string>, "expiration_date": <YYYY-MM-DD>},\n'
            "  ...\n"
            "]\n"
            "DO NOT include any explanation before or after the JSON."
        )

        if not content_type:
            content_type = "image/jpeg"  # Default if not provided

        try:
            response = self.client.chat.completions.create(
                model="gpt-5-nano-2025-08-07",  # Or your preferred current vision model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{content_type};base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_completion_tokens=1500,
                temperature=0.5,
            )

            # Log the full OpenAI vision response for debugging
            print("\n👁️ OpenAI Vision API Response:")
            print("   Model: gpt-4o (vision)")
            print(f"   Usage: {response.usage}")
            print(f"   Response ID: {response.id}")

            vision_result = response.choices[0].message.content.strip()
            print("   Vision Result Preview:")
            print(f"   {vision_result[:300]}...")
            print(f"   Full Result Length: {len(vision_result)} characters\n")

            return vision_result

        except Exception as e:
            print(f"Error communicating with OpenAI API: {e}")  # Log the actual error
            raise RuntimeError(f"Error communicating with OpenAI API: {str(e)}") from e

    def parse_openai_response(self, response_text: str) -> list[dict[str, Any]]:
        """
        Parses the JSON response from OpenAI and extracts pantry items.
        Combines duplicate items and sums their quantities.
        Returns a list of pantry items with their details.
        """
        today = datetime.today().date()
        records = []
        item_dict = {}  # Dictionary to track unique items

        cleaned_text = response_text.strip()
        # Enhanced cleaning for potential markdown code blocks
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[len("```json") :].strip()
        if cleaned_text.startswith("```"):  # Catch if only ``` is used
            cleaned_text = cleaned_text[len("```") :].strip()
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[: -len("```")].strip()

        try:
            items = json.loads(cleaned_text)
            if not isinstance(items, list):
                # Handle cases where the response might be a single dict instead of a list of dicts
                if isinstance(items, dict):
                    items = [items]  # Convert to list if it's a single item
                else:
                    print(
                        f"OpenAI response is not a JSON array or dictionary as expected. Raw: {cleaned_text}"
                    )
                    raise ValueError(
                        "OpenAI response is not a JSON array or dictionary as expected."
                    )
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON. Raw text: '{cleaned_text}'. Error: {e}")
            raise ValueError(f"Failed to decode JSON from OpenAI response. Content: {cleaned_text}")

        for item in items:
            if not isinstance(item, dict):
                print(f"Skipping non-dictionary item in JSON array: {item}")
                continue

            item_name = item.get("item_name", "Unknown Item")
            quantity_str = item.get("quantity", "1 unit")  # Default if not provided
            count = item.get("count", 1)  # Get count, default to 1 if not provided
            category = item.get(
                "category", "Other"
            )  # Get category, default to "Other" if not provided
            expiration_date_str = item.get("expiration_date")

            quantity_amount = 1.0
            quantity_unit = "unit"  # Default unit

            if quantity_str:
                # Updated regex to capture number and the rest as unit/description
                match = re.match(r"([\d\.]+)\s*(.*)", str(quantity_str).strip())
                if match:
                    try:
                        quantity_amount = float(match.group(1))
                        parsed_unit = match.group(2).strip()
                        quantity_unit = parsed_unit or "unit"
                    except ValueError:
                        print(
                            f"Could not parse quantity amount from: '{match.group(1)}' for item '{item_name}'"
                        )
                        quantity_amount = 1.0
                        quantity_unit = str(quantity_str).strip()
                else:
                    print(
                        f"Could not parse quantity string: '{quantity_str}' for item '{item_name}' using regex. Using original as unit."
                    )
                    quantity_amount = 1.0
                    quantity_unit = str(quantity_str).strip()

            expected_expiry_date = today + timedelta(days=7)  # Default if no date
            if expiration_date_str:
                try:
                    expected_expiry_date = datetime.strptime(expiration_date_str, "%Y-%m-%d").date()
                except ValueError:
                    print(
                        f"Could not parse expiration date '{expiration_date_str}' for item '{item_name}'. Using default."
                    )

            # Create a unique key for the item based on name and unit
            item_key = f"{item_name}|{quantity_unit}"

            if item_key in item_dict:
                # If item exists, update the quantity and count
                item_dict[item_key]["quantity_amount"] += quantity_amount
                item_dict[item_key]["count"] += count
                # Keep the earlier expiration date
                if (
                    expected_expiry_date
                    < datetime.strptime(
                        item_dict[item_key]["expected_expiration"], "%Y-%m-%d"
                    ).date()
                ):
                    item_dict[item_key]["expected_expiration"] = expected_expiry_date.isoformat()
            else:
                # If item doesn't exist, add it to the dictionary
                item_dict[item_key] = {
                    "item_name": item_name,
                    "quantity_amount": quantity_amount,
                    "quantity_unit": quantity_unit,
                    "category": category,
                    "count": count,
                    "expected_expiration": expected_expiry_date.isoformat(),
                }

        # Convert the dictionary values to a list
        records = list(item_dict.values())
        return records
