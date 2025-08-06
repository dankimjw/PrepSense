import asyncio
import os

import cachetools
import httpx

API_KEY = os.getenv("SPOONACULAR_KEY")
BASE = "https://api.spoonacular.com/recipes"

cache = cachetools.TTLCache(maxsize=5_000, ttl=60 * 60 * 24 * 14)  # 14 days


async def search_by_ingredients(ingredients: list[str], number: int = 20):
    key = ("search", ",".join(sorted(ingredients)))
    if key in cache:
        return cache[key]
    q = ",".join(ingredients)
    url = f"{BASE}/findByIngredients"
    async with httpx.AsyncClient(timeout=10) as cli:
        r = await cli.get(url, params={"ingredients": q, "number": number, "apiKey": API_KEY})
    r.raise_for_status()
    cache[key] = r.json()
    return cache[key]


async def get_recipe_information(recipe_id: int):
    if recipe_id in cache:
        return cache[recipe_id]
    url = f"{BASE}/{recipe_id}/information"
    async with httpx.AsyncClient(timeout=10) as cli:
        r = await cli.get(url, params={"includeNutrition": True, "apiKey": API_KEY})
    r.raise_for_status()
    cache[recipe_id] = r.json()
    return cache[recipe_id]
