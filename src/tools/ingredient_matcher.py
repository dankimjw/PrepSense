import re
import string

from rapidfuzz import fuzz, process


def canonicalise(raw: str) -> str:
    """Lowercase, strip punctuation / stop words."""
    import inflect

    p = inflect.engine()
    txt = raw.lower().translate(str.maketrans("", "", string.punctuation))
    words = [w for w in txt.split() if w not in {"organic", "fresh"}]
    return " ".join([p.singular_noun(w) or w for w in words])


def match_and_score(recipe_ing, pantry):
    idx = {p["canonical_name"]: p for p in pantry}
    matches = []
    for ing in recipe_ing:
        target = canonicalise(ing["name"])
        name, sim = process.extractOne(target, idx.keys(), scorer=fuzz.WRatio)
        if sim < 75:
            continue
        p = idx[name]
        if p["canon_unit"] != ing["canon_unit"]:
            continue
        have, need = p["qty_canon"], ing["qty_canon"]
        matches.append(dict(item_id=p["item_id"], need=need, have=have, score=min(1, have / need)))
    return matches
