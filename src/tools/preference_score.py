def score(recipe, prefs):
    """
    Very lightweight scoring:
    +0.4 if cuisine matches
    +0.4 if no allergen violation
    +0.2 macro-fit
    Returns (score 0-1, explain str)
    """
    score, reasons = 0, []
    if prefs.get("cuisines") and recipe.get("cuisine") in prefs["cuisines"]:
        score += 0.4
        reasons.append("preferred cuisine")
    if any(a in recipe.get("allergens", []) for a in prefs.get("allergens", [])):
        reasons.append("allergen conflict")
        return 0, ", ".join(reasons)
    else:
        score += 0.4
    if prefs.get("calorie_target"):
        diff = abs(recipe.get("calories", 0) - prefs["calorie_target"])
        if diff < 100:
            score += 0.2
            reasons.append("macro fit")
    return score, ", ".join(reasons or ["basic match"])
