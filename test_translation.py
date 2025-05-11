import os
import sys
import requests
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

def test_openai_api_key():
    """Test if the OpenAI API key is valid by making a simple API call."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return False, "API key not set"
    
    # Ensure the API key is properly formatted
    api_key = api_key.strip()
    
    # Test with a simple API call
    try:
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code == 200:
            return True, "API key is valid"
        elif response.status_code == 401:
            return False, "Invalid API key"
        else:
            return False, f"API error: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Error testing API key: {str(e)}"

def main():
    """
    Test the translation functionality.
    """
    print("Testing Translation Service")
    print("==========================")
    
    # Check if API key is valid
    api_key = os.environ.get("OPENAI_API_KEY")
    print(f"API Key set: {bool(api_key)}")
    
    if api_key:
        print(f"API Key value: {api_key[:4]}...{api_key[-4:] if len(api_key) > 8 else ''}")
        is_valid, message = test_openai_api_key()
        print(f"API Key valid: {is_valid} - {message}")
    
    # Test with real API (may fail if quota exceeded or API key invalid)
    print("\n1. Testing with real API:")
    print("------------------------")
    translation_service = TranslationService()
    
    # Test text translation
    test_text = "Hello, this is a test message. We are testing the translation functionality."
    target_language = "es"  # Spanish
    
    print(f"Translating text to {target_language}...")
    try:
        translated_text = translation_service.translate_text(test_text, target_language)
        print("\nOriginal text:")
        print(test_text)
        print("\nTranslated text:")
        print(translated_text)
    except Exception as e:
        print(f"Error during translation: {str(e)}")
    
    # Test with mock translation (should always work)
    print("\n2. Testing with mock translation:")
    print("-------------------------------")
    mock_translation_service = TranslationService(use_mock=True)
    
    print(f"Translating text to {target_language} using mock...")
    try:
        mock_translated_text = mock_translation_service.translate_text(test_text, target_language)
        print("\nOriginal text:")
        print(test_text)
        print("\nMock translated text:")
        print(mock_translated_text)
        
        # Test a few more languages with mock
        for lang, lang_name in [("fr", "French"), ("de", "German")]:
            print(f"\nTranslating to {lang_name} ({lang}) using mock:")
            mock_result = mock_translation_service.translate_text(test_text, lang)
            print(mock_result)
    except Exception as e:
        print(f"Error during mock translation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
