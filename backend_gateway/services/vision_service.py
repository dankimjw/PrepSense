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

    async def classify_food_items(self, base64_image: str, content_type: Optional[str]) -> str:
        """
        Sends the base64-encoded image to OpenAI's API with a detailed prompt.
        Returns the raw JSON response string from OpenAI.
        """
        today_str = datetime.today().strftime("%Y-%m-%d")
        prompt_text = (
            f"You are a grocery inventory assistant helping track food items.\n\n"
            f"Today's date is {today_str}.\n\n"
            "Instructions:\n"
            "- For each food item visible in the image:\n"
            "  - Identify the full brand name and product type as the item_name (e.g., 'Neilson TruTaste 1% Milk', 'PC Greek Yogurt').\n"
            "  - Identify quantity and packaging size (e.g., '2 kg bag', '1 L bottle', '15 oz can').\n" # Added example
            "  - Find a visible Best Before (BB), Use By, or Expiry date on the package.\n"
            "  - If no printed date is found, estimate expiration based on the type of item.\n"
            "Return a STRICT JSON array ONLY like:\n"
            "[\n"
            "  {{\"item_name\": <string>, \"quantity\": <string>, \"expiration_date\": <YYYY-MM-DD date>}},\n"
            "  ...\n"
            "]\n"
            "NO extra explanations, NO text before or after the JSON."
        )

        if not content_type:
            content_type = "image/jpeg" # Default if not provided

        try:
            # Ensure this API call matches your OpenAI library version (older vs newer)
            # This example assumes older library version (pre v1.0.0) due to previous contexts
            # If you upgraded, use self.client.chat.completions.create(...)
            if hasattr(openai, 'OpenAI'): # Check if it's v1.0.0+ structure
                 client = openai.OpenAI(api_key=self.api_key)
                 response = await client.chat.completions.create(
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
                response = await openai.ChatCompletion.acreate(
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
        Returns a list of pantry items with their details.
        """
        today = datetime.today().date()
        records = []

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
            expiration_date_str = item.get("expiration_date")

            quantity_amount = 1.0
            quantity_unit = "unit" # Default unit

            if quantity_str:
                # Updated regex to capture number and the rest as unit/description
                # Uses re.match to match from the beginning of the string
                match = re.match(r"([\d\.]+)\s*(.*)", str(quantity_str).strip())
                if match:
                    try:
                        quantity_amount = float(match.group(1))
                        # group(2) will now contain things like "oz can", "kg bag", "slices", etc.
                        # If group(2) is empty, it means only a number was provided.
                        parsed_unit = match.group(2).strip()
                        if parsed_unit: # Check if there's anything after the number
                            quantity_unit = parsed_unit
                        else: # Only a number was found, use default "unit" or a more specific default
                            quantity_unit = "unit" # Or perhaps "item(s)" if only a number
                    except ValueError:
                        print(f"Could not parse quantity amount from: '{match.group(1)}' for item '{item_name}'")
                        # Fallback to default if conversion fails
                        quantity_amount = 1.0
                        quantity_unit = str(quantity_str).strip() # Use the original string as unit in this case
                else:
                     print(f"Could not parse quantity string: '{quantity_str}' for item '{item_name}' using regex. Using original as unit.")
                     # If regex doesn't match at all, use the original string as the unit and default amount
                     quantity_amount = 1.0 # Or try to parse the whole string as a number if it makes sense
                     quantity_unit = str(quantity_str).strip()


            expected_expiry_date = today + timedelta(days=7) # Default if no date
            if expiration_date_str:
                try:
                    expected_expiry_date = datetime.strptime(expiration_date_str, "%Y-%m-%d").date()
                except ValueError:
                    print(f"Could not parse expiration date '{expiration_date_str}' for item '{item_name}'. Using default.")

            records.append({
                "item_name": item_name,
                "quantity_amount": quantity_amount,
                "quantity_unit": quantity_unit,
                "date_added": today.isoformat(),
                "expected_expiration": expected_expiry_date.isoformat()
            })
        return records

