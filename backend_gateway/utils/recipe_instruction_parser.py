"""
Recipe instruction parser utility to group instructions into logical sections.
"""
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup


def parse_instructions_to_groups(instructions: str, max_groups: int = 3) -> List[Dict[str, Any]]:
    """
    Parse recipe instructions into logical groups (2-3 sections).
    
    Args:
        instructions: HTML or plain text instructions
        max_groups: Maximum number of groups to create (default 3)
    
    Returns:
        List of instruction groups with titles and steps
    """
    if not instructions:
        return []
    
    # Parse HTML if present
    if instructions.startswith('<'):
        soup = BeautifulSoup(instructions, 'html.parser')
        # Extract list items
        steps = []
        for li in soup.find_all('li'):
            text = li.get_text().strip()
            if text and text.lower() != 'method:':
                steps.append(text)
    else:
        # Plain text - split by common delimiters
        steps = re.split(r'[\n\r]+|\d+\.|\d+\)', instructions)
        steps = [s.strip() for s in steps if s.strip()]
    
    if not steps:
        return []
    
    # Group steps into logical sections
    groups = []
    
    # Define keywords for different cooking phases
    prep_keywords = ['mash', 'mix', 'add', 'combine', 'shape', 'spread', 'dip', 'coat', 'roll']
    cook_keywords = ['cook', 'bake', 'fry', 'boil', 'heat', 'microwave', 'refrigerate', 'chill']
    finish_keywords = ['serve', 'garnish', 'plate', 'top', 'drizzle']
    
    prep_steps = []
    cook_steps = []
    finish_steps = []
    
    for step in steps:
        step_lower = step.lower()
        
        # Categorize based on keywords
        if any(keyword in step_lower for keyword in finish_keywords):
            finish_steps.append(step)
        elif any(keyword in step_lower for keyword in cook_keywords):
            cook_steps.append(step)
        else:
            # Default to prep if no specific keywords
            prep_steps.append(step)
    
    # Build groups based on available steps
    if prep_steps:
        groups.append({
            "title": "Preparation",
            "steps": prep_steps,
            "time_estimate": f"{len(prep_steps) * 3} mins"
        })
    
    if cook_steps:
        # Estimate cooking time based on keywords
        time_est = "20 mins"
        if any('refrigerate' in s.lower() or 'chill' in s.lower() for s in cook_steps):
            time_est = "30+ mins"
        elif any('bake' in s.lower() for s in cook_steps):
            time_est = "20-30 mins"
        
        groups.append({
            "title": "Cooking",
            "steps": cook_steps,
            "time_estimate": time_est
        })
    
    if finish_steps:
        groups.append({
            "title": "Finishing",
            "steps": finish_steps,
            "time_estimate": "2 mins"
        })
    
    # If we have too many groups, consolidate
    if len(groups) > max_groups:
        # Merge the smallest groups
        while len(groups) > max_groups:
            # Find smallest group
            min_idx = min(range(len(groups)), key=lambda i: len(groups[i]["steps"]))
            
            # Merge with adjacent group
            if min_idx > 0:
                groups[min_idx - 1]["steps"].extend(groups[min_idx]["steps"])
                groups.pop(min_idx)
            elif min_idx < len(groups) - 1:
                groups[min_idx]["steps"].extend(groups[min_idx + 1]["steps"])
                groups.pop(min_idx + 1)
    
    # If we have only one group, try to split it
    if len(groups) == 1 and len(groups[0]["steps"]) > 3:
        all_steps = groups[0]["steps"]
        mid = len(all_steps) // 2
        
        groups = [
            {
                "title": "Preparation",
                "steps": all_steps[:mid],
                "time_estimate": f"{mid * 3} mins"
            },
            {
                "title": "Cooking & Finishing",
                "steps": all_steps[mid:],
                "time_estimate": "20 mins"
            }
        ]
    
    return groups


def format_grouped_instructions(groups: List[Dict[str, Any]]) -> str:
    """
    Format grouped instructions into a readable string.
    
    Args:
        groups: List of instruction groups
    
    Returns:
        Formatted string with grouped instructions
    """
    if not groups:
        return "No instructions available"
    
    formatted = []
    for i, group in enumerate(groups, 1):
        formatted.append(f"**{group['title']}** (~{group['time_estimate']})")
        for j, step in enumerate(group['steps'], 1):
            formatted.append(f"  {j}. {step}")
        formatted.append("")  # Empty line between groups
    
    return "\n".join(formatted).strip()


# Example usage for the Salmon Croquettes recipe
if __name__ == "__main__":
    sample_instructions = """<ol><li>Method:</li><li>Cook potatoes in microwave or in a large pot of boiling water until tender, drain.</li><li>Mash potatoes in a large bowl, add egg yolk and butter stir to combine.</li><li>Then add in salmon or Tuna flakes mix well and add salt and pepper to taste.</li><li>Spread some plain flour on to a small tray.</li><li>Shape potatoes into a small oval shape and roll them in the plain flour, shake off excess.</li><li>Dip into lightly beaten egg white, coat with flaked almonds, pressing them on firmly.</li><li>Place on prepared baking lined tray and refrigerate for 30 mins.</li><li>Bake at preheated oven 200C for 20 mins or until golden.</li><li>Serve with mayo and mustard sauce.</li></ol>"""
    
    groups = parse_instructions_to_groups(sample_instructions)
    print(format_grouped_instructions(groups))
