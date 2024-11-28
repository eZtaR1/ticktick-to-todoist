"""
Utility functions for the TickTick to Todoist converter.
"""
import re
from pathlib import Path
from typing import Union

def clean_label_name(name: str) -> str:
    """
    Convert a string into a valid Todoist label by removing spaces and special characters.
    
    Args:
        name: The original string to convert
        
    Returns:
        A cleaned string suitable for use as a Todoist label
    """
    # Replace spaces with underscores and remove special characters
    cleaned = re.sub(r'[^\w\s-]', '', name)
    cleaned = cleaned.replace(' ', '_')
    return cleaned.lower()

def ensure_path(path: Union[str, Path]) -> Path:
    """
    Convert string path to Path object and ensure it exists.
    
    Args:
        path: String or Path object representing a file path
        
    Returns:
        Path object
        
    Raises:
        FileNotFoundError: If the path doesn't exist
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    return path_obj
