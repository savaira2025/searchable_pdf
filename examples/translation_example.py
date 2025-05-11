"""
Example script demonstrating the translation functionality of the Searchable PDF Library.
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document.processor import PDFProcessor
from core.translation.translator import TranslationService

def main():
    """
    Run the translation example.
    """
    print("Searchable PDF Library - Translation Example")
    print("===========================================")
    
    # Check if API key is set
    api_key = os.environ.get("OPENAI_API_KEY")
    use_mock = False
    
    if not api_key:
        print("\nNo OpenAI API key found in environment variables.")
        print("You can set it using:")
        print("  export OPENAI_API_KEY=your_api_key_here  # Linux/macOS")
        print("  set OPENAI_API_KEY=your_api_key_here     # Windows")
        
        mock_option = input("\nWould you like to use mock translation for testing? (y/n): ")
        if mock_option.lower() == 'y':
            use_mock = True
            print("Using mock translation for testing.")
        else:
            print("Proceeding with real API (may fail without a valid API key).")
    
    # Initialize components
    pdf_processor = PDFProcessor()
    translation_service = TranslationService(use_mock=use_mock)
    
    if use_mock:
        print("\nNOTE: Using mock translation. Translations will be prefixed with [MOCK TRANSLATION]")
        print("      and only common words/phrases will be translated.")
    
    # List available documents
    documents = pdf_processor.list_documents(limit=5)
    
    if not documents["documents"]:
        print("\nNo documents found. Please upload a document first.")
        return
    
    print(f"\nFound {len(documents['documents'])} documents:")
    for i, doc in enumerate(documents["documents"]):
        print(f"{i+1}. {doc['title'] or doc['filename']} (ID: {doc['id']})")
    
    # Select a document
    try:
        selection = int(input("\nSelect a document to translate (enter number): ")) - 1
        if selection < 0 or selection >= len(documents["documents"]):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input. Please enter a number.")
        return
    
    document_id = documents["documents"][selection]["id"]
    document_title = documents["documents"][selection]["title"] or documents["documents"][selection]["filename"]
    
    print(f"\nSelected document: {document_title}")
    
    # Select target language
    languages = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "zh": "Chinese",
        "ja": "Japanese",
        "ru": "Russian",
        "ar": "Arabic"
    }
    
    print("\nAvailable target languages:")
    for code, name in languages.items():
        print(f"{code}: {name}")
    
    target_language = input("\nEnter target language code (e.g., 'es' for Spanish): ")
    
    if target_language not in languages:
        print(f"Warning: '{target_language}' is not in the list of supported languages. Proceeding anyway.")
    
    # Translate document
    print(f"\nTranslating document to {target_language}...")
    
    try:
        result = translation_service.translate_document(document_id, target_language)
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return
        
        print("\nTranslation completed successfully!")
        print(f"Source language: {result['source_language']}")
        print(f"Target language: {result['target_language']}")
        
        if result.get("cached", False):
            print("(Translation loaded from cache)")
        elif result.get("skipped", False):
            print("(Translation skipped - document already in target language)")
        
        # Display a preview of the translation
        preview_length = 500
        translated_text = result["translated_text"]
        preview = translated_text[:preview_length] + ("..." if len(translated_text) > preview_length else "")
        
        print("\nTranslation preview:")
        print("-------------------")
        print(preview)
        print("-------------------")
        
        # Save translation to a file
        output_file = f"{document_id}_{target_language}_translation.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(translated_text)
        
        print(f"\nFull translation saved to: {output_file}")
        
    except Exception as e:
        print(f"Error during translation: {str(e)}")

if __name__ == "__main__":
    main()
