"""
Utility module for handling optional imports.
This allows the library to function even when certain packages are not installed.
"""

import importlib
import sys
from typing import Any, Dict, Optional, Tuple, Union


def is_package_available(package_name: str) -> bool:
    """
    Check if a package is available for import.
    
    Args:
        package_name: The name of the package to check.
        
    Returns:
        True if the package is available, False otherwise.
    """
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False


def optional_import(
    package_name: str,
    error_message: Optional[str] = None
) -> Tuple[Any, bool]:
    """
    Import a package if it's available, otherwise return None.
    
    Args:
        package_name: The name of the package to import.
        error_message: Optional message to print if the package is not available.
        
    Returns:
        A tuple containing the imported module (or None if not available) and a boolean
        indicating whether the import was successful.
    """
    try:
        module = importlib.import_module(package_name)
        return module, True
    except ImportError:
        if error_message:
            print(f"Warning: {error_message}")
        return None, False


# Define commonly used optional packages
spacy, HAS_SPACY = optional_import(
    "spacy", 
    "spaCy is not installed. NLP features will be limited."
)

nltk, HAS_NLTK = optional_import(
    "nltk", 
    "NLTK is not installed. NLP features will be limited."
)

pandas, HAS_PANDAS = optional_import(
    "pandas", 
    "pandas is not installed. Data analysis features will be limited."
)

numpy, HAS_NUMPY = optional_import(
    "numpy", 
    "NumPy is not installed. Some numerical operations will be limited."
)

# Image processing packages
pillow, HAS_PILLOW = optional_import(
    "PIL", 
    "Pillow is not installed. Image processing features will be limited."
)

pytesseract, HAS_PYTESSERACT = optional_import(
    "pytesseract", 
    "pytesseract is not installed. OCR features will be unavailable."
)

# Search packages
whoosh, HAS_WHOOSH = optional_import(
    "whoosh", 
    "Whoosh is not installed. Search functionality will be limited."
)

# Define feature availability flags
HAS_NLP = HAS_SPACY or HAS_NLTK
HAS_DATA_ANALYSIS = HAS_PANDAS or HAS_NUMPY
HAS_OCR = HAS_PILLOW and HAS_PYTESSERACT
HAS_SEARCH = HAS_WHOOSH
