# REMOVED API KEY FOR SECURITY

# from openai import OpenAI

# client = OpenAI(api_key="YOUR_API_KEY_HERE")


# response = client.completions.create(engine="text-davinci-003",
# prompt="Once upon a time",
# max_tokens=60)

# print(response.choices[0].text.strip())


# import os, dotenv, pathlib
# dotenv.load_dotenv(pathlib.Path(".env"))
# print(os.getenv("OPENAI_API_KEY"))

from openai import OpenAI

# show first/last 4 chars only
# openai_key_loader_example.py
from backend_gateway.core.config_utils import get_openai_api_key

api_key = get_openai_api_key()  # ← same logic used by OCR router, etc.
client = OpenAI(api_key=api_key)

# quick smoke-test
print("Key starts with:", api_key[:8], "...")  # don’t print the whole key
print(client.models.list())  # cheapest authenticated call
