#!/usr/bin/env python3
"""Setup OpenAI API key from JSON config"""

import json
import os

# Read from JSON file
with open('config/openai.json', 'r') as f:
    config = json.load(f)
    api_key = config.get('openai_key')

# Write to expected text file
with open('config/openai_key.txt', 'w') as f:
    f.write(api_key)

print("OpenAI API key has been set up in config/openai_key.txt")