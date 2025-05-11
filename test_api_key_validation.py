"""
Simple script to test the API key validation in the TranslationService.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Force reload of environment variables
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv(override=True)
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")

from core.translation.translator import TranslationService

def main():
    """
    Test the API key validation in the TranslationService.
    """
    print("Testing API Key Validation")
    print("=========================")
    
    # Check if API key is set in environment
    api_key = os.environ.get("OPENAI_API_KEY")
    print(f"API Key set: {bool(api_key)}")
    
    if api_key:
        print(f"API Key value: {api_key[:4]}...{api_key[-4:] if len(api_key) > 8 else ''}")
    else:
        print("API Key value: None")
    
    # Initialize the translation service
    translation_service = TranslationService()
    
    # Test text translation
    test_text = "Hello, this is a test message. We are testing the translation functionality."
    target_language = "es"  # Spanish
    
    print(f"\nTranslating text to {target_language}...")
    translated_text = translation_service.translate_text(test_text, target_language)
    
    print("\nOriginal text:")
    print(test_text)
    print("\nTranslated text:")
    print(translated_text)
    
    # Check if the translation contains the expected error message
    if "[Translation error: API key not found" in translated_text:
        print("\nSuccess: The API key validation is working correctly!")
    else:
        print("\nWarning: The API key validation might not be working as expected.")

if __name__ == "__main__":
    main()
