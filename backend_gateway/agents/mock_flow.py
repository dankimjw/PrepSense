"""Mock classes for CrewAI flow functionality not available in v0.1.32"""

class Flow:
    """Mock Flow class"""
    def __init__(self, *args, **kwargs):
        pass

def listen(*args, **kwargs):
    """Mock listen decorator"""
    def decorator(func):
        return func
    return decorator

def start(*args, **kwargs):
    """Mock start decorator"""
    def decorator(func):
        return func
    return decorator
