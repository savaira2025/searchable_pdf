"""
Example script demonstrating multilingual search capabilities using the Searchable PDF Library.
This example shows how to translate search queries and results across languages.
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document.processor import PDFProcessor
from core.search.engine import SearchEngine
from core.translation.translator import TranslationService

def main():
    """
    Run the multilingual search example.
    """
    print("Searchable PDF Library - Multilingual Search Example")
    print("==================================================")
    
    # Check if API key is set
    api_key = os.environ.get("OPENAI_API_KEY")
    use_mock = False
    
    if not api_key:
        print("\nNo OpenAI API key found in environment variables.")
        print("Translation features may not work correctly without an API key.")
        
        mock_option = input("\nWould you like to use mock translation for testing? (y/n): ")
        if mock_option.lower() == 'y':
            use_mock = True
            print("Using mock translation for testing.")
        else:
            print("Proceeding with real API (may fail without a valid API key).")
    
    # Initialize components
    pdf_processor = PDFProcessor()
    search_engine = SearchEngine()
    translation_service = TranslationService(use_mock=use_mock)
    
    if use_mock:
        print("\nNOTE: Using mock translation. Translations will be prefixed with [MOCK TRANSLATION]")
        print("      and only common words/phrases will be translated.")
    
    # Get user input
    query = input("\nEnter search query: ")
    if not query:
        print("No query provided. Exiting.")
        return
    
    # Detect query language
    query_language = translation_service.detect_language(query)
    print(f"Detected query language: {query_language}")
    
    # Perform search with original query
    print(f"\nSearching with original query: '{query}'")
    search_results = search_engine.search(query, limit=5)
    
    if search_results.total_results == 0:
        print("No results found with original query.")
        
        # Try translating the query to English for better search results
        if query_language != "en":
            print(f"\nTranslating query to English for better search...")
            translated_query = translation_service.translate_text(query, "en", query_language)
            print(f"Translated query: '{translated_query}'")
            
            # Search with translated query
            search_results = search_engine.search(translated_query, limit=5)
            
            if search_results.total_results == 0:
                print("No results found with translated query either.")
                return
            else:
                print(f"\nFound {search_results.total_results} results with translated query:")
        else:
            return
    else:
        print(f"\nFound {search_results.total_results} results:")
    
    # Display search results
    for i, result in enumerate(search_results.results):
        print(f"\n{i+1}. {result.document_title or result.document_filename}")
        print(f"   Document ID: {result.document_id}")
        print(f"   Score: {result.score}")
        
        if result.highlight:
            print(f"   Context: {result.highlight}")
    
    # Ask if user wants to translate results
    if search_results.total_results > 0:
        translate_option = input("\nWould you like to translate the results? (y/n): ")
        
        if translate_option.lower() == 'y':
            # Get target language
            target_language = input("Enter target language code (e.g., 'es' for Spanish): ")
            
            print(f"\nTranslating search results to {target_language}...")
            
            # Get the first result document for demonstration
            result = search_results.results[0]
            document_id = result.document_id
            
            try:
                # Extract text from the document
                doc = pdf_processor.get_document(document_id)
                if not doc:
                    print(f"Document not found: {document_id}")
                    return
                
                text = pdf_processor.get_document_text(document_id)
                if not text:
                    print(f"No text found in document: {document_id}")
                    return
                
                # Detect document language
                doc_language = translation_service.detect_language(text[:1000])
                print(f"Detected document language: {doc_language}")
                
                # Translate a snippet of the document
                snippet_length = 500
                snippet = text[:snippet_length] + ("..." if len(text) > snippet_length else "")
                
                print("\nOriginal snippet:")
                print("----------------")
                print(snippet)
                
                # Translate the snippet
                translated_snippet = translation_service.translate_text(
                    snippet, 
                    target_language, 
                    doc_language
                )
                
                print(f"\nTranslated snippet ({doc_language} to {target_language}):")
                print("----------------")
                print(translated_snippet)
                
                # Save translation to a file
                output_file = f"{document_id}_{target_language}_translation.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(translated_snippet)
                
                print(f"\nTranslation snippet saved to: {output_file}")
                
            except Exception as e:
                print(f"Error during translation: {str(e)}")

if __name__ == "__main__":
    main()
