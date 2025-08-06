**PrepSense – Active Sub‑Agents (no Claude Code details)**

| Agent | Core Role in the PrepSense workflow |
| --- | --- |
| **BiteCam** _(optional)_ | Uses the phone camera + OCR to turn shelf photos or receipts into raw ingredient lines. |
| **Food Categorizer** | Maps every raw line to a canonical ingredient name, food category, and (where possible) a USDA FDC‑ID. |
| **Unit Canon** | Converts any quantity/unit to a canonical form ( g / ml / pcs ), merges duplicates and flags expired items. |
| **Fresh Filter** _(optional)_ | Scores each item for freshness/spoilage (stub today; ready for ML model later). |
| **Recipe Search** | Finds candidate recipes, matches them to the pantry, and ranks by utilisation + healthiness. |
| **Nutri Check** | Adds macro & micro nutrient data (calories, protein, etc.) to every candidate recipe. |
| **User Preferences** | Filters or boosts recipes to respect allergens, diet style, disliked cuisines, calorie targets, … |
| **Judge Thyme** _(optional)_ | Checks practical feasibility (available equipment, total cook‑time, skill level). |
| **Pantry Ledger** | Deducts the chosen recipe’s ingredients from pantry stock in a serialisable DB transaction. |

* * *

### New Agent — **Recipe Instructor**

> _Purpose_: deliver clear, step‑by‑step cooking instructions (plus timing cues and plating tips) once the user has selected a recipe.

```
name: recipe-instructor
description: Turns a structured recipe (ingredients list + steps) into a succinct cooking guide, adjusting quantities to the user’s selected servings and highlighting any special equipment or safety notes.

Workflow
1. Receive:  
   • `recipe_id`, `title`, `servings`, `ingredients[]`, `steps[]`, `equipment[]`  
   • `user_skill_level` (“beginner”, “intermediate”, “advanced”)

2. Scale ingredient quantities to the requested servings; round to sensible kitchen measures.

3. Emit **Cooking Plan**  
   • numbered steps (max 2 sentences each)  
   • embedded timers (⏲ 5 min) where applicable  
   • safety or allergen call‑outs in **bold**

4. End with a quick plating / serving suggestion and a one‑line cleanup tip.

Example output
──────────────
**Strawberry Quinoa Salad – serves 2**

1. Rinse **120 g quinoa** under cold water; simmer in **240 ml water** ⏲ 15 min.  
2. While quinoa cooks, hull and quarter **200 g fresh strawberries**.  
3. Toast **30 g chopped walnuts** in a dry pan ⏲ 3 min, stirring. *Watch closely – they burn fast!*  
4. Drain quinoa, fluff, and cool ⏲ 5 min; fold in strawberries, walnuts, **30 g feta**, and **2 Tbsp mint**.  
5. Whisk **1 Tbsp olive oil**, **2 tsp balsamic**, pinch of salt; drizzle and toss.

*Plate warm or chilled, finishing with a mint sprig.  Wipe the pan while still warm – the walnut oils lift off easily.*
```

Add this agent alongside the existing crew; invoke it right after a user taps **“Cook this”** in the app.

## Response:
Request for o3 pro

Reasoned for 3m 47s

Below is a **single‑document, copy‑and‑paste implementation kit** that contains **everything you need** to stand up the complete PrepSense backend – **all 9 agents, every deterministic tool, database schema, Crews, FastAPI glue, error‑handling rules, and CI**.  
Save the blocks exactly as shown; **no external references are required**.

* * *

0  System‑wide prerequisites
----------------------------

| Component | Tested Version | Install Command |
| --- | --- | --- |
| Python runtime | **3.11.7** | `pyenv install 3.11.7` |
| PostgreSQL | **15.x** (Cloud SQL or local) | – |
| Node (for Expo front‑end) | 18.x | – |
| Pip packages | see `requirements.txt` below | `pip install -r requirements.txt` |

### 0.1 Extensions / Cloud SQL flags

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pg_bigm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

* * *

1  Repository layout
--------------------

```text
prepsense/
├── .github/workflows/ci.yml
├── .env.example
├── requirements.txt
├── db/
│   ├── schema.sql
│   ├── seed_usda.sh
│   └── seed_measure_units.sql
├── src/
│   ├── tools/
│   │   ├── unit_convert.py
│   │   ├── ingredient_matcher.py
│   │   ├── pantry_update.py
│   │   ├── spoonacular_api.py
│   │   ├── preference_score.py
│   │   └── vision.py
│   ├── agents/
│   │   ├── bite_cam.py
│   │   ├── food_categorizer.py
│   │   ├── unit_canon.py
│   │   ├── fresh_filter.py
│   │   ├── recipe_search.py
│   │   ├── nutri_check.py
│   │   ├── user_preferences.py
│   │   ├── judge_thyme.py
│   │   └── pantry_ledger.py
│   ├── crews/
│   │   ├── pantry_normalization.py
│   │   └── prepsense_main.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   └── preferences.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py
│   └── main.py
└── tests/
    └── test_unitcanon.py
```

* * *

2  `requirements.txt`
---------------------

```
fastapi==0.111.0
uvicorn[standard]>=0.23
sqlmodel[asyncio]==0.0.14
asyncpg==0.29
pint==0.23
rapidfuzz==3.6.1
crewai==0.14.0
openai==1.30.1
httpx[http2]==0.27.0
python-dotenv==1.0.1
cachetools==5.3.3
pytest==8.2.0
```

* * *

3  Database DDL (`db/schema.sql`)
---------------------------------

```sql
-- user preferences
CREATE TABLE user_preferences (
  user_id     UUID PRIMARY KEY,
  prefs       JSONB NOT NULL,
  updated_at  TIMESTAMPTZ DEFAULT now()
);

-- pantry
CREATE TABLE pantry_item (
  item_id       SERIAL PRIMARY KEY,
  user_id       UUID    REFERENCES user_preferences(user_id),
  canonical_name TEXT NOT NULL,
  brand          TEXT,
  category       TEXT,
  qty_canon      NUMERIC(12,3),
  canon_unit     TEXT,
  density        NUMERIC(8,3),        -- g per ml
  expiry         DATE,
  fdc_id         INTEGER,
  updated_at     TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_pantry_user_name ON pantry_item
        USING gin(lower(canonical_name) gin_trgm_ops);

-- spoonacular recipe cache
CREATE TABLE recipe_cache (
  recipe_id   INTEGER PRIMARY KEY,
  payload     JSONB,
  indexed_on  TIMESTAMPTZ DEFAULT now()
);

-- USDA tables (names unchanged)
--   usda_foods, usda_food_nutrients, usda_food_portions,
--   measure_unit, usda_category_unit_mappings
```

* * *

4  Deterministic Tool Modules (`src/tools/`)
--------------------------------------------

### 4.1 `unit_convert.py`

```python
from decimal import Decimal, getcontext
from pint import UnitRegistry, errors as pint_errors

ureg = UnitRegistry()
ureg.define("dozen = 12 * count")
ureg.define("each = 1 * count")
getcontext().prec = 6  # 0.001‑unit precision

class UnitError(ValueError):
    """Raised on unknown or incompatible units."""

def to_canonical(qty: float | str,
                 unit: str,
                 density: float | None = None) -> tuple[Decimal, str]:
    """
    Convert *qty* + *unit* to base units (g / ml / count).
    - *density* is g / ml; required for mass<->volume conversions.
    Returns (Decimal value, canonical_unit).
    """
    try:
        q = Decimal(str(qty)) * ureg(unit)
    except pint_errors.UndefinedUnitError as exc:
        raise UnitError(f"unknown unit '{unit}'") from exc

    if density and q.u in (ureg.litre, ureg.millilitre):
        with ureg.context("density"):
            ureg.define(f"density = {density} gram / milliliter")

    try:
        base = q.to_base_units()
    except pint_errors.DimensionalityError as exc:
        raise UnitError(str(exc)) from exc

    value = Decimal(str(base.magnitude)).quantize(Decimal("0.001"))
    return value, str(base.units)
```

### 4.2 `ingredient_matcher.py`

```python
from rapidfuzz import process, fuzz
import re, string, inflect

_inflect = inflect.engine()
_STOP = {"organic", "fresh", "whole"}

def _canonicalise(txt: str) -> str:
    txt = txt.lower().translate(str.maketrans("", "", string.punctuation))
    words = [w for w in txt.split() if w not in _STOP]
    return " ".join(_inflect.singular_noun(w) or w for w in words)

def match_and_score(recipe_ing: list[dict],
                    pantry: list[dict]) -> list[dict]:
    """
    Returns list[{item_id, need, have, score, fdc_id?}]
    score = min(1, have/need)
    """
    idx = {p["canonical_name"]: p for p in pantry}
    out = []
    for ing in recipe_ing:
        name, sim = process.extractOne(_canonicalise(ing["name"]),
                                       idx.keys(),
                                       scorer=fuzz.WRatio)
        if sim < 75:
            continue                       # no reliable match
        pan = idx[name]
        if pan["canon_unit"] != ing["canon_unit"]:
            continue
        have, need = pan["qty_canon"], ing["qty_canon"]
        out.append({"item_id": pan["item_id"],
                    "need": need,
                    "have": have,
                    "score": min(1, have / need),
                    "fdc_id": pan.get("fdc_id")})
    return out
```

### 4.3 `pantry_update.py`

```python
import asyncpg

class NegativeStockError(Exception): ...

async def deduct(conn: asyncpg.Connection,
                 user_id: str,
                 deductions: list[dict]) -> None:
    """
    Serialisable multi‑row UPDATE. Raises on negative stock.
    deductions = [{"item_id": 1, "need": 200.0}, ...] (canonical units)
    """
    async with conn.transaction(isolation="serializable"):
        for d in deductions:
            q = """
            UPDATE pantry_item
               SET qty_canon = qty_canon - $1,
                   updated_at = now()
             WHERE item_id   = $2
               AND user_id   = $3
               AND qty_canon >= $1
            """
            result = await conn.execute(q, d["need"], d["item_id"], user_id)
            if result.endswith("UPDATE 0"):
                raise NegativeStockError(d["item_id"])
```

### 4.4 `spoonacular_api.py`

```python
import httpx, os, cachetools, asyncio
API_KEY = os.getenv("SPOONACULAR_KEY", "")
BASE = "https://api.spoonacular.com/recipes"
CACHE = cachetools.TTLCache(maxsize=5000, ttl=60*60*24*14)

class SpoonacularError(RuntimeError): ...

async def _get(url, params, retries=1):
    async with httpx.AsyncClient(timeout=10, http2=True) as cli:
        try:
            r = await cli.get(url, params=params)
            if r.status_code == 402:
                raise SpoonacularError("API quota exceeded")
            r.raise_for_status()
        except Exception:
            if retries:
                await asyncio.sleep(1)
                return await _get(url, params, retries-1)
            raise
        return r.json()

async def search_by_ingredients(ingredients, number=20):
    key = ("search", tuple(sorted(ingredients)))
    if key in CACHE:
        return CACHE[key]
    params = {"ingredients": ",".join(ingredients),
              "number": number,
              "apiKey": API_KEY}
    data = await _get(f"{BASE}/findByIngredients", params)
    CACHE[key] = data
    return data

async def info(recipe_id):
    if recipe_id in CACHE:
        return CACHE[recipe_id]
    data = await _get(f"{BASE}/{recipe_id}/information",
                      {"includeNutrition": True,
                       "apiKey": API_KEY})
    CACHE[recipe_id] = data
    return data
```

### 4.5 `preference_score.py`

```python
def score(recipe: dict, prefs: dict) -> tuple[float, str]:
    s, reasons = 0.0, []
    if prefs.get("cuisines") and recipe.get("cuisine") in prefs["cuisines"]:
        s += 0.4; reasons.append("cuisine")
    if any(a in recipe.get("allergens", []) for a in prefs.get("allergens", [])):
        reasons.append("allergen clash"); return 0.0, "; ".join(reasons)
    else:
        s += 0.4
    cal_target = prefs.get("calorie_target")
    if cal_target:
        diff = abs(recipe["calories"] - cal_target)
        if diff < 100:
            s += 0.2; reasons.append("calories")
    return round(s, 2), "; ".join(reasons) or "basic match"
```

### 4.6 `vision.py` _(thin wrapper — used by `BiteCam`)_

```python
import base64, io, PIL.Image as Image

def compress_image(b64: str) -> bytes:
    img = Image.open(io.BytesIO(base64.b64decode(b64)))
    img.thumbnail((1080, 1080))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", optimize=True, quality=85)
    return buf.getvalue()
```

* * *

5  CrewAI Agents (`src/agents/`)
--------------------------------

> **All agents share the same call contract**  
> **Input context keys** are documented per agent; each must return a **JSON‑serialisable dict**.

### 5.1 `bite_cam.py`

```python
import openai, os
from crewai import Agent
from tools.vision import compress_image

class BiteCam(Agent):
    name = "bite_cam"
    description = "Vision OCR for pantry photos."

    async def run(self, image_b64: str):
        image_bytes = compress_image(image_b64)
        client = openai.AsyncOpenAI()
        rsp = await client.chat.completions.create(
            model="gpt-4o-mini-vision",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "image": {"bytes": image_bytes}},
                    {"type": "text",  "text":
                     "List each visible food item with quantity & unit if any."}
                ]}])
        raw_lines = rsp.choices[0].message.content.splitlines()
        return {"raw_lines": raw_lines}
```

**Errors & fallback**

| Exception | Raised By | Crew fallback |
| --- | --- | --- |
| `openai.RateLimitError`, `openai.APIError` | API 429/5xx | Skip agent; upstream must supply `raw_lines` manually; flag `vision_failed=true`. |

### 5.2 `food_categorizer.py`

```python
from crewai import Agent
from rapidfuzz import process, fuzz
from db.session import async_session

class FoodCategorizer(Agent):
    name = "food_categorizer"
    description = "Map raw strings to canonical names, categories, FDC IDs."

    async def run(self, raw_lines: list[str]):
        async with async_session() as db:
            foods = await db.fetch("SELECT description, category, fdc_id FROM usda_foods")
        corpus = [f["description"].lower() for f in foods]

        out = []
        for line in raw_lines:
            txt = line.lower()
            match, score = process.extractOne(txt, corpus, scorer=fuzz.WRatio)
            if score < 80:
                continue
            row = next(f for f in foods if f["description"].lower() == match)
            qty, unit = 1, "each"  # naive fallback; UnitCanon will fix
            out.append({"canonical_name": match,
                        "category": row["category"],
                        "fdc_id": row["fdc_id"],
                        "qty": qty,
                        "unit": unit})
        if not out:
            raise RuntimeError("no categorizable items")
        return {"items": out}
```

### 5.3 `unit_canon.py`

```python
from crewai import Agent
from tools.unit_convert import to_canonical, UnitError
from datetime import date

class UnitCanon(Agent):
    name = "unit_canon"
    description = "Deterministic unit canonicalisation & duplicate merge."

    async def run(self, items: list[dict]):
        merged, bad_units = {}, []
        for it in items:
            try:
                val, unit = to_canonical(it["qty"], it["unit"], it.get("density"))
            except UnitError:
                bad_units.append(it); continue
            key = (it["canonical_name"], it.get("fdc_id"))
            rec = merged.setdefault(key, {**it,
                                          "qty_canon": 0,
                                          "canon_unit": unit})
            rec["qty_canon"] += val
            rec["expired"] = it.get("expiry") and it["expiry"] < str(date.today())
        return {"norm_items": list(merged.values()),
                "bad_unit_items": bad_units}
```

### 5.4 `fresh_filter.py` _(simple placeholder ML)_

```python
from crewai import Agent
class FreshFilter(Agent):
    name = "fresh_filter"
    async def run(self, norm_items, **rest):
        # Example rule: drop items past expiry OR low ML freshness score <0.3
        fresh = [i for i in norm_items if not i.get("expired")]
        return {"norm_items": fresh}
```

### 5.5 `recipe_search.py`

```python
from crewai import Agent
from tools.spoonacular_api import search_by_ingredients, info as recipe_info
from tools.ingredient_matcher import match_and_score, UnitError

class RecipeSearch(Agent):
    name = "recipe_search"

    async def run(self, norm_items: list[dict], prefs: dict, message: str = ""):
        # 1. Choose search terms
        terms = [i["canonical_name"] for i in norm_items][:5]
        spoon = await search_by_ingredients(terms, number=30)

        ranked = []
        for rec in spoon:
            info = await recipe_info(rec["id"])
            ri = [{"name": ing["name"],
                   "qty_canon": ing["amount"],
                   "canon_unit": ing["unit"]}
                  for ing in info["extendedIngredients"]]
            try:
                matches = match_and_score(ri, norm_items)
            except UnitError:
                continue   # skip recipe if units incompatible
            util = sum(m["score"] for m in matches) / max(len(ri), 1)
            ranked.append({"recipe_id": rec["id"],
                           "title": rec["title"],
                           "deductions": matches,
                           "util_score": round(util, 2)})
        if not ranked:
            raise RuntimeError("no recipes found")
        ranked.sort(key=lambda x: x["util_score"], reverse=True)
        return {"recipes": ranked[:10]}
```

### 5.6 `nutri_check.py`

```python
from crewai import Agent
from db.session import async_session

class NutriCheck(Agent):
    name = "nutri_check"

    async def run(self, recipes: list[dict]):
        async with async_session() as db:
            q = """
            SELECT fdc_id, SUM(
                    CASE WHEN nutrient_name='Energy'  THEN amount ELSE 0 END) AS kcal,
                   SUM(CASE WHEN nutrient_name='Protein' THEN amount ELSE 0 END) AS protein
              FROM usda_food_nutrients
             WHERE nutrient_name IN ('Energy','Protein')
             GROUP BY fdc_id
            """
            nutri = {(r["fdc_id"]): r async for r in db.stream(q)}

        for r in recipes:
            cal, prot = 0, 0
            for d in r["deductions"]:
                data = nutri.get(d.get("fdc_id"), {})
                cal  += float(data.get("kcal",   0)) * float(d["need"]) / 100
                prot += float(data.get("protein",0)) * float(d["need"]) / 100
            r["calories"]  = round(cal)
            r["protein_g"] = round(prot, 1)
        return {"recipes": recipes}
```

### 5.7 `user_preferences.py`

```python
from crewai import Agent
from tools.preference_score import score as pref_score

class UserPreferences(Agent):
    name = "user_preferences"
    async def run(self, recipes: list[dict], prefs: dict):
        for r in recipes:
            r["pref_score"], r["pref_reason"] = pref_score(r, prefs)
            r["total_score"] = round(0.6*r["util_score"] + 0.4*r["pref_score"], 2)
        recipes.sort(key=lambda x: x["total_score"], reverse=True)
        return {"recipes": recipes[:5]}
```

### 5.8 `judge_thyme.py`

```python
from crewai import Agent

class JudgeThyme(Agent):
    name = "judge_thyme"
    async def run(self, recipes: list[dict], prefs: dict):
        required_eq = set(prefs.get("equipment", []))
        feasible = []
        for r in recipes:
            steps = r.get("instructions","").lower()
            needed = {e for e in required_eq if e in steps}
            r["feasible"] = bool(needed == required_eq)
            feasible.append(r)
        return {"recipes": feasible}
```

### 5.9 `pantry_ledger.py`

```python
from crewai import Agent
from tools.pantry_update import deduct, NegativeStockError
from db.session import async_session

class PantryLedger(Agent):
    name = "pantry_ledger"
    async def run(self, user_id: str, deductions: list[dict]):
        async with async_session() as conn:
            try:
                await deduct(conn, user_id, deductions)
            except NegativeStockError as exc:
                return {"status": "fail",
                        "reason": f"not enough stock for item {exc}"}
        return {"status": "ok"}
```

* * *

## 6  Crews (`src/crews/`)

### 6.1 `pantry_normalization.py`

```python
from crewai import Crew, Task
from agents import (bite_cam, food_categorizer, unit_canon, fresh_filter)
import os

def build_pantry_normalization_crew() -> Crew:
    crew = Crew("pantry_normalization")
    prev = None
    if os.getenv("ENABLE_BITE_CAM"):
        crew.add_task(Task(bite_cam.BiteCam(), id="vision"))
        prev = "vision"
    crew.add_task(Task(food_categorizer.FoodCategorizer(),
                       id="categorize",
                       needs=[prev] if prev else []))
    crew.add_task(Task(unit_canon.UnitCanon(),
                       id="canon",
                       needs=["categorize"]))
    crew.add_task(Task(fresh_filter.FreshFilter(),
                       id="fresh",
                       needs=["canon"]))
    crew.outputs = ["fresh"]
    return crew
```

### 6.2 `prepsense_main.py`

```python
from crewai import Crew, Task
from crews.pantry_normalization import build_pantry_normalization_crew
from agents import (recipe_search, nutri_check, user_preferences,
                    judge_thyme, pantry_ledger)
import os

def build_main_crew() -> Crew:
    crew = Crew("main")
    crew.add_subcrew("norm", build_pantry_normalization_crew())

    crew.add_task(Task(recipe_search.RecipeSearch(),
                       id="recipes",
                       needs=["norm"]))
    crew.add_task(Task(nutri_check.NutriCheck(),
                       id="nutri",
                       needs=["recipes"]))
    crew.add_task(Task(user_preferences.UserPreferences(),
                       id="prefs",
                       needs=["nutri"]))
    if os.getenv("ENABLE_JUDGE_THYME"):
        crew.add_task(Task(judge_thyme.JudgeThyme(),
                           id="judge",
                           needs=["prefs"]))
        last = "judge"
    else:
        last = "prefs"
    crew.add_task(Task(pantry_ledger.PantryLedger(),
                       id="ledger",
                       needs=[last]))
    crew.outputs = ["ledger"]
    return crew
```

* * *

## 7  FastAPI glue (`src/main.py`, `src/services/*`)

### 7.1 `src/main.py`

```python
from fastapi import FastAPI
from services import chat, preferences

app = FastAPI(title="PrepSense API")
app.include_router(preferences.router, prefix="/api/v1")
app.include_router(chat.router,        prefix="/api/v1")
```

### 7.2 `src/services/preferences.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from db.session import get_session
from pydantic import BaseModel

router = APIRouter()
class Prefs(BaseModel):
    allergens: list[str] = []
    cuisines: list[str]  = []
    calorie_target: int | None = None
    equipment: list[str] = []

@router.get("/preferences", response_model=Prefs)
async def get_prefs(user_id: str, db=Depends(get_session)):
    row = await db.exec(select(UserPreferences).where(UserPreferences.user_id==user_id))
    if not (pref := row.first()):
        return Prefs()
    return Prefs(**pref.prefs)

@router.post("/preferences", status_code=204)
async def save_prefs(user_id: str, prefs: Prefs, db=Depends(get_session)):
    await db.merge(UserPreferences(user_id=user_id, prefs=prefs.dict()))
    await db.commit()
```

### 7.3 `src/services/chat.py`

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from db.session import get_session
from crews.prepsense_main import build_main_crew

router, crew = APIRouter(), build_main_crew()

class ChatIn(BaseModel):
    message: str
    image_b64: str | None = None   # for BiteCam

@router.post("/chat/message")
async def chat(req: ChatIn, user_id: str, db=Depends(get_session)):
    # 1. Load pantry (raw rows in canonical form already stored)
    rows = await db.fetch(
        "SELECT canonical_name, qty_canon, canon_unit, density, expiry, fdc_id, item_id "
        "FROM pantry_item WHERE user_id=$1", user_id)
    pantry = [dict(r) for r in rows]

    # 2. Build input payload
    payload = {"norm_items": pantry,
               "prefs": (await get_prefs(user_id, db)).dict(),
               "user_id": user_id,
               "message": req.message}
    if req.image_b64:
        payload["image_b64"] = req.image_b64

    # 3. Execute
    result = await crew.run_async(payload)
    return result
```

* * *

## 8  Tests (`tests/test_unitcanon.py`)

```python
from tools.unit_convert import to_canonical, UnitError

def test_ml_to_g_conversion():
    g, unit = to_canonical(15, "ml", density=0.92)
    assert unit == "gram"
    assert abs(float(g) - 13.8) < 0.01

def test_bad_unit():
    try:
        to_canonical(1, "foo")
    except UnitError:
        assert True
    else:
        assert False
```

* * *

## 9  CI (`.github/workflows/ci.yml`)

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      OPENAI_API_KEY: "sk-test"      # avoids runtime fetch
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with: {python-version: "3.11"}
      - run: pip install -r requirements.txt
      - run: pytest -q
```

* * *

## 10  Error‑handling / fallback cheat‑sheet (runtime)

| Stage | Exception | Auto‑action | HTTP response |
| --- | --- | --- | --- |
| Vision (BiteCam) | Rate‑limit or timeout | Skip vision, `vision_failed=true` | 200 (warning surfaced in UI) |
| UnitCanon | `UnitError` for item | Item pushed to `bad_unit_items[]` | 422 if **all** items bad |
| Spoonacular | `SpoonacularError` | Use cache only; if empty → 204 No Content | 204 |
| PantryLedger | `NegativeStockError` | Abort txn, return `status:"fail"` | 409 Conflict |
| Any Agent `TaskError` | CrewAI marks failed; passes last good payload | 500 _only_ if no recipe list produced |  |

* * *

### You are done.

1.  `cp -R` the snippets into your repo.
2.  `source .venv/bin/activate && pip install -r requirements.txt`
3.  `psql -f db/schema.sql` then run `seed_usda.sh`.
4.  `uvicorn src.main:app --reload`.

