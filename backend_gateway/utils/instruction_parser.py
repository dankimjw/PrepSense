"""
Utility to improve recipe instruction parsing and formatting
"""
import re
from typing import List, Dict, Any


def clean_instruction_step(step_text: str) -> str:
    """
    Clean and format a single instruction step.
    
    Args:
        step_text: Raw instruction text
        
    Returns:
        Cleaned instruction text
    """
    if not step_text:
        return ""
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', step_text.strip())
    
    # Ensure proper sentence ending
    if cleaned and not cleaned.endswith(('.', '!', '?')):
        cleaned += '.'
    
    return cleaned


def split_long_instruction(step_text: str, max_length: int = 200) -> List[str]:
    """
    Split overly long instructions into smaller, manageable steps.
    
    Args:
        step_text: Long instruction text
        max_length: Maximum length for a single step
        
    Returns:
        List of shorter instruction steps
    """
    if not step_text or len(step_text) <= max_length:
        return [clean_instruction_step(step_text)]
    
    steps = []
    
    # Split on common instruction delimiters
    delimiters = [
        r'(?<=\.)\s+(?=[A-Z])',  # After period followed by capital letter
        r'(?<=:)\s*(?=[A-Z])',   # After colon followed by capital letter
        r'\.\s*(?=Making)',      # Before "Making" (like "Making the Caramel")
        r'\.\s*(?=Preparing)',   # Before "Preparing"
        r'\.\s*(?=To\s)',        # Before "To" (like "To serve")
        r'\.\s*(?=Once)',        # Before "Once"
        r'\.\s*(?=Meanwhile)',   # Before "Meanwhile"
        r'\.\s*(?=Then)',        # Before "Then"
    ]
    
    current_text = step_text
    
    for delimiter in delimiters:
        parts = re.split(delimiter, current_text)
        if len(parts) > 1:
            # If splitting helped, use the parts
            for part in parts:
                part = part.strip()
                if part:
                    if len(part) > max_length:
                        # Recursively split if still too long
                        steps.extend(split_long_instruction(part, max_length))
                    else:
                        steps.append(clean_instruction_step(part))
            return steps
    
    # If no delimiters worked, split on sentences
    sentences = re.split(r'(?<=\.)\s+', current_text)
    current_step = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        if len(current_step + " " + sentence) <= max_length:
            current_step = (current_step + " " + sentence).strip()
        else:
            if current_step:
                steps.append(clean_instruction_step(current_step))
            current_step = sentence
    
    if current_step:
        steps.append(clean_instruction_step(current_step))
    
    return steps if steps else [clean_instruction_step(step_text)]


def improve_recipe_instructions(analyzed_instructions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Improve recipe instructions by cleaning and splitting long steps.
    
    Args:
        analyzed_instructions: Original analyzed instructions from Spoonacular
        
    Returns:
        Improved instructions with better step breakdown
    """
    if not analyzed_instructions:
        return []
    
    improved_instructions = []
    
    for instruction_group in analyzed_instructions:
        if not instruction_group.get('steps'):
            continue
            
        improved_group = instruction_group.copy()
        improved_steps = []
        step_number = 1
        
        for step in instruction_group['steps']:
            step_text = step.get('step', '')
            if not step_text:
                continue
            
            # Split long steps into multiple steps
            split_steps = split_long_instruction(step_text)
            
            for split_step in split_steps:
                improved_step = step.copy()
                improved_step['step'] = split_step
                improved_step['number'] = step_number
                improved_steps.append(improved_step)
                step_number += 1
        
        improved_group['steps'] = improved_steps
        improved_instructions.append(improved_group)
    
    return improved_instructions


def extract_step_actions(step_text: str) -> List[str]:
    """
    Extract key actions from an instruction step.
    
    Args:
        step_text: Instruction text
        
    Returns:
        List of key actions/verbs
    """
    if not step_text:
        return []
    
    # Common cooking actions
    cooking_actions = [
        'mix', 'stir', 'whisk', 'beat', 'fold', 'combine', 'blend',
        'chop', 'dice', 'slice', 'mince', 'grate', 'shred',
        'heat', 'cook', 'bake', 'roast', 'fry', 'saute', 'boil', 'simmer',
        'add', 'pour', 'sprinkle', 'season', 'taste', 'adjust',
        'cover', 'uncover', 'wrap', 'refrigerate', 'freeze',
        'serve', 'garnish', 'plate', 'drizzle'
    ]
    
    found_actions = []
    text_lower = step_text.lower()
    
    for action in cooking_actions:
        if re.search(r'\b' + action + r'\b', text_lower):
            found_actions.append(action)
    
    return found_actions[:3]  # Limit to top 3 actions