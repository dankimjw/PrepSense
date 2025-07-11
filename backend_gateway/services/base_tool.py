"""
Base tool class for compatibility with different CrewAI versions
"""

from typing import Any, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict


class BaseTool(BaseModel):
    """
    Base class for tools that can be used by agents.
    Compatible with both old and new CrewAI versions.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='allow')
    
    name: str = Field(..., description="The unique name of the tool")
    description: str = Field(..., description="A description of what the tool does")
    
    def __init__(self, **data):
        """Initialize with any additional fields"""
        super().__init__(**data)
    
    async def _run(self, *args, **kwargs) -> Any:
        """
        The main method that executes the tool's functionality.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement the _run method")
    
    def run(self, *args, **kwargs) -> Any:
        """
        Synchronous wrapper for the async _run method.
        """
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # If loop is already running (e.g., in Jupyter), create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, self._run(*args, **kwargs))
                return future.result()
        else:
            return loop.run_until_complete(self._run(*args, **kwargs))