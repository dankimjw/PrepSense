# File: PrepSense/backend_gateway/services/vision_service.py
import base64
import openai # Or from openai import OpenAI if you upgraded to v1.0.0+
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
import json
from typing import Optional, Tuple, List, Dict, Any

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
    def __init__(self, api_key: str = None):
        """
        Initializes the VisionService with an OpenAI API key.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found. Please set it in your .env file or pass it to the constructor.")
        
        # Initialize the client based on your OpenAI library version
        # If using openai < 1.0.0, you might set openai.api_key globally or pass it around
        # If using openai >= 1.0.0, initialize the client instance:
        # from openai import OpenAI # at the top of the file
        # self.client = OpenAI(api_key=self.api_key)
        # For this example, assuming older library or global setup for simplicity of focus on parse method

    async def process_image(self, file) -> Tuple[str, Optional[str]]:
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
            "  2. Scan the package for quantity indicators. These are often found next to weight (g, kg), volume (ml, L), or counts (e.g., '6-pack').\n"
            "     - Convert all quantity details into a consistent quantity string (e.g., '500 g pack', '1.5 L bottle', '6 eggs').\n"
            "     - Extract numerical value and unit separately.\n"
            "       Examples:\n"
            "         '1.5 L bottle' -> quantity_amount: 1.5, quantity_unit: 'L'\n"
            "         '6 pack' -> quantity_amount: 6, quantity_unit: 'units'\n"
            "  3. Item Count Details:\n"
            "     - For each distinct food item type identified, carefully count all visible units of that exact item in the image.\n"
            "     - This total visual count should be an integer, and you must include it in the 'count' field for that item's JSON object.\n"
            "     - For example, if there are 5 identical cans of 'Joe's O's Cereal' visible, the 'count' field for that item's entry must be 5.\n"
            "     - Please ensure the 'count' field is always present in each item's JSON object.\n"
            "  4. Look for any printed expiration date.\n"
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
            "  {\"item_name\": <string>, \"quantity\": <string>, \"count\": <integer>, \"expiration_date\": <YYYY-MM-DD>},\n"
            "  ...\n"
            "]\n"
            "DO NOT include any explanation before or after the JSON."
        )

        if not content_type:
            content_type = "image/jpeg" # Default if not provided

        try:
            if hasattr(openai, 'OpenAI'): # Check if it's v1.0.0+ structure
                 client = openai.OpenAI(api_key=self.api_key)
                 response = client.chat.completions.create(
                    model="gpt-4o", # Or your preferred current vision model
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
                    max_tokens=1500,
                    temperature=0.5,
                )
                 return response.choices[0].message.content.strip()
            else: # Older library
                openai.api_key = self.api_key # Ensure API key is set for older library
                response = openai.ChatCompletion.create(
                    model="gpt-4o", # Or your preferred current vision model
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
                    max_tokens=1500,
                    temperature=0.5,
                )
                return response.choices[0].message['content'].strip()

        except Exception as e:
            print(f"Error communicating with OpenAI API: {e}") # Log the actual error
            raise RuntimeError(f"Error communicating with OpenAI API: {str(e)}")

    def parse_openai_response(self, response_text: str) -> List[Dict[str, Any]]:
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
            cleaned_text = cleaned_text[len("```json"):].strip()
        if cleaned_text.startswith("```"): # Catch if only ``` is used
            cleaned_text = cleaned_text[len("```"):].strip()
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-len("```")].strip()

        try:
            items = json.loads(cleaned_text)
            if not isinstance(items, list):
                 # Handle cases where the response might be a single dict instead of a list of dicts
                 if isinstance(items, dict):
                     items = [items] # Convert to list if it's a single item
                 else:
                    print(f"OpenAI response is not a JSON array or dictionary as expected. Raw: {cleaned_text}")
                    raise ValueError("OpenAI response is not a JSON array or dictionary as expected.")
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON. Raw text: '{cleaned_text}'. Error: {e}")
            raise ValueError(f"Failed to decode JSON from OpenAI response. Content: {cleaned_text}")

        for item in items:
            if not isinstance(item, dict):
                print(f"Skipping non-dictionary item in JSON array: {item}")
                continue

            item_name = item.get("item_name", "Unknown Item")
            quantity_str = item.get("quantity", "1 unit") # Default if not provided
            count = item.get("count", 1) # Get count, default to 1 if not provided
            expiration_date_str = item.get("expiration_date")

            quantity_amount = 1.0
            quantity_unit = "unit" # Default unit

            if quantity_str:
                # Updated regex to capture number and the rest as unit/description
                match = re.match(r"([\d\.]+)\s*(.*)", str(quantity_str).strip())
                if match:
                    try:
                        quantity_amount = float(match.group(1))
                        parsed_unit = match.group(2).strip()
                        if parsed_unit:
                            quantity_unit = parsed_unit
                        else:
                            quantity_unit = "unit"
                    except ValueError:
                        print(f"Could not parse quantity amount from: '{match.group(1)}' for item '{item_name}'")
                        quantity_amount = 1.0
                        quantity_unit = str(quantity_str).strip()
                else:
                     print(f"Could not parse quantity string: '{quantity_str}' for item '{item_name}' using regex. Using original as unit.")
                     quantity_amount = 1.0
                     quantity_unit = str(quantity_str).strip()

            expected_expiry_date = today + timedelta(days=7) # Default if no date
            if expiration_date_str:
                try:
                    expected_expiry_date = datetime.strptime(expiration_date_str, "%Y-%m-%d").date()
                except ValueError:
                    print(f"Could not parse expiration date '{expiration_date_str}' for item '{item_name}'. Using default.")

            # Create a unique key for the item based on name and unit
            item_key = f"{item_name}|{quantity_unit}"
            
            if item_key in item_dict:
                # If item exists, update the quantity and count
                item_dict[item_key]["quantity_amount"] += quantity_amount
                item_dict[item_key]["count"] += count
                # Keep the earlier expiration date
                if expected_expiry_date < datetime.strptime(item_dict[item_key]["expected_expiration"], "%Y-%m-%d").date():
                    item_dict[item_key]["expected_expiration"] = expected_expiry_date.isoformat()
            else:
                # If item doesn't exist, add it to the dictionary
                item_dict[item_key] = {
                    "item_name": item_name,
                    "quantity_amount": quantity_amount,
                    "quantity_unit": quantity_unit,
                    "count": count,
                    "date_added": today.isoformat(),
                    "expected_expiration": expected_expiry_date.isoformat()
                }

        # Convert the dictionary values to a list
        records = list(item_dict.values())
        return records
