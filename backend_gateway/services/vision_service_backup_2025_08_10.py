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
            "- CRITICAL: Create ONE entry for EACH physical item you see, even if they are identical.\n"
            "- If you see 2 identical cans of beans, you MUST create 2 separate entries with the same item_name.\n"
            "- If you see 3 bottles of the same juice, you MUST create 3 separate entries.\n"
            "- NEVER combine multiple items into a single entry with quantity like '2 cans' or '3 bottles'.\n"
            "- The JSON array length should equal the number of physical items visible.\n"
            "- For each individual item visible:\n"
            "  1. Read all visible text and branding on the packaging to identify the full item name.\n"
            "     - Include brand and type (e.g., 'Oasis Orange Juice', 'Great Value Basmati Rice').\n"
            "  2. The 'quantity' field should ONLY contain the size printed on ONE package (e.g., '16 oz', '1 gallon').\n"
            "     - NEVER put counts like '2 cans' or '3 bottles' in the quantity field\n"
            "     - Use the unit printed on the package when available\n"
            "     - For produce without labels, estimate weight or use 'each' for a single item\n"
            "     - Common units: oz, lb, gallon, liter, can, bottle, jar, loaf, dozen, each\n"
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
            '  {"item_name": <string>, "quantity": <string>, "category": <string>, "expiration_date": <YYYY-MM-DD>},\n'
            "  ...\n"
            "]\n\n"
            "EXAMPLE - How to count identical items:\n"
            "If you see in the image:\n"
            "- 2 cans of Campbell's Tomato Soup (each 10.75 oz)\n"
            "Then, <1st entry 10.75 oz>, <2nd entry 10.75 oz>\n"
            "You MUST return 2 total entries (2):\n"
            "[\n"
            '  {"item_name": "Campbell\'s Tomato Soup", "quantity": "10.75 oz", "category": "Canned Goods", "expiration_date": "2025-12-01"},\n'
            '  {"item_name": "Campbell\'s Tomato Soup", "quantity": "10.75 oz", "category": "Canned Goods", "expiration_date": "2025-12-01"},\n'
            '  {"item_name": "Coca-Cola", "quantity": "20 oz", "category": "Beverages", "expiration_date": "2025-09-15"},\n'
            '  {"item_name": "Coca-Cola", "quantity": "20 oz", "category": "Beverages", "expiration_date": "2025-09-15"},\n'
            '  {"item_name": "Coca-Cola", "quantity": "20 oz", "category": "Beverages", "expiration_date": "2025-09-15"},\n'
            '  {"item_name": "Wonder Bread", "quantity": "20 oz", "category": "Bakery", "expiration_date": "2025-08-17"}\n'
            "]\n\n"
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
                temperature=0.5,
            )

            # Log the full OpenAI vision response for debugging
            print("\n👁️ OpenAI Vision API Response:")
            print("   Model: gpt-5-nano-2025-08-07 (vision)")
            print(f"   Usage: {response.usage}")
            print(f"   Response ID: {response.id}")

            # Handle potential None response
            message_content = response.choices[0].message.content
            if message_content is None:
                print("   ⚠️ Warning: OpenAI returned None content")
                print(f"   Full response: {response}")
                raise RuntimeError("OpenAI API returned empty response content")

            vision_result = message_content.strip()
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
        Returns a list of pantry items with their details.
        """
        today = datetime.today().date()
        records = []

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

            # Add each item directly to records without deduplication
            record = {
                "item_name": item_name,
                "quantity_amount": quantity_amount,
                "quantity_unit": quantity_unit,
                "category": category,
                "expected_expiration": expected_expiry_date.isoformat(),
            }
            records.append(record)
        return records
