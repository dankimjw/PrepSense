import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_recipe():
    prompt = "Generate a recipe using pantry items..."
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()