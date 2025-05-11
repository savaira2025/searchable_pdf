"""
Example script demonstrating how to set up and use the translation functionality
with a valid OpenAI API key in the Searchable PDF Library.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

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
    Run the translation API key example.
    """
    print("Searchable PDF Library - Translation API Key Example")
    print("==================================================")
    
    # Check if API key is set in environment
    api_key = os.environ.get("OPENAI_API_KEY")
    use_mock = False
    
    if not api_key:
        print("\nNo OpenAI API key found in environment variables.")
        print("You can set it using:")
        print("  export OPENAI_API_KEY=your_api_key_here  # Linux/macOS")
        print("  set OPENAI_API_KEY=your_api_key_here     # Windows")
        
        # Offer options: enter API key or use mock translation
        print("\nOptions:")
        print("1. Enter an OpenAI API key")
        print("2. Use mock translation for testing (no API key required)")
        option = input("Enter your choice (1 or 2): ")
        
        if option == "1":
            # Prompt for API key
            api_key = input("\nEnter your OpenAI API key (starts with 'sk-' or 'sk-proj-'): ")
            if api_key:
                # Set the API key in the environment
                os.environ["OPENAI_API_KEY"] = api_key.strip()
                print("API key set for this session.")
            else:
                print("No API key provided.")
                use_mock = True
                print("Falling back to mock translation for testing.")
        else:
            use_mock = True
            print("Using mock translation for testing.")
    
    # Initialize the translation service
    translation_service = TranslationService(use_mock=use_mock)
    
    if use_mock:
        print("\nNOTE: Using mock translation. Translations will be prefixed with [MOCK TRANSLATION]")
        print("      and only common words/phrases will be translated.")
    
    # Test text translation
    test_text = "Hello, this is a test message. We are testing the translation functionality."
    target_language = input("\nEnter target language code (e.g., 'es' for Spanish): ") or "es"
    
    print(f"\nTranslating text to {target_language}...")
    try:
        translated_text = translation_service.translate_text(test_text, target_language)
        
        # Check if translation was successful (doesn't start with "[Translation error")
        if not translated_text.startswith("[Translation error"):
            print("\nTranslation successful!")
            print("\nOriginal text:")
            print(test_text)
            print("\nTranslated text:")
            print(translated_text)
            
            if not use_mock:
                print("\nYour OpenAI API key is working correctly for translation!")
                print("You can now use the translation functionality in the library.")
            else:
                print("\nMock translation is working correctly.")
                print("To use real translation, set a valid OpenAI API key.")
        else:
            print("\nTranslation failed:")
            print(translated_text)
            print("\nPlease check your API key and try again, or use mock translation for testing.")
    except Exception as e:
        print(f"\nError during translation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
