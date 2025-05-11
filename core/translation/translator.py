import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import requests
from datetime import datetime

# Try to import dotenv for loading environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")

class TranslationService:
    """
    Handles translation of document content using LLM models.
    Supports both API-based and local model translation.
    """
    
    def __init__(self, base_dir: str = "storage", use_api: bool = True, use_mock: bool = False):
        self.base_dir = Path(base_dir)
        self.translations_dir = self.base_dir / "translations"
        self.translations_dir.mkdir(parents=True, exist_ok=True)
        
        self.use_mock = use_mock
        self.use_api = use_api and not use_mock
        self.api_key = os.environ.get("OPENAI_API_KEY")  # or other API key
        
        # Print a warning if API key is not set and we're not using mock
        if self.use_api and not self.api_key and not self.use_mock:
            print("Warning: OPENAI_API_KEY environment variable not set. Translation will not work.")
            print("Consider using mock translation for testing by setting use_mock=True")
        
        # Load local model if not using API and not using mock
        if not self.use_api and not self.use_mock:
            try:
                # Import and load appropriate translation model
                # This is a placeholder - in a real implementation, you would load a model
                # like NLLB or M2M100 using the transformers library
                print("Note: Local translation model support is not implemented")
                if not self.use_mock:
                    self.use_api = True  # Fall back to API if not using mock
            except ImportError as e:
                print(f"Warning: Could not load local translation model: {e}")
                if not self.use_mock:
                    self.use_api = True  # Fall back to API if not using mock
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the provided text.
        
        Args:
            text: Text to analyze
            
        Returns:
            ISO language code (e.g., 'en', 'es', 'fr')
        """
        try:
            # Try to use langdetect if available
            try:
                from langdetect import detect
                return detect(text)
            except ImportError:
                pass
            
            # Fallback to a simple regex-based approach
            # This is very basic and only detects a few languages
            # In a real implementation, you would use a more robust method
            
            # Check for common characters in different scripts
            if re.search(r'[\u4e00-\u9fff]', text):  # Chinese
                return "zh"
            elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):  # Japanese
                return "ja"
            elif re.search(r'[\u0600-\u06ff]', text):  # Arabic
                return "ar"
            elif re.search(r'[\u0400-\u04ff]', text):  # Cyrillic (Russian, etc.)
                return "ru"
            
            # Default to English
            return "en"
        except:
            return "en"  # Default to English if detection fails
    
    def _mock_translate(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> str:
        """
        Provide a mock translation for testing purposes.
        This doesn't actually translate the text but adds markers to indicate
        it would have been translated.
        
        Args:
            text: Text to "translate"
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Mock translated text
        """
        # Simple mock translations for common phrases in a few languages
        mock_translations = {
            # English to Spanish
            ("en", "es", "Hello"): "Hola",
            ("en", "es", "World"): "Mundo",
            ("en", "es", "Thank you"): "Gracias",
            ("en", "es", "Welcome"): "Bienvenido",
            ("en", "es", "Goodbye"): "Adiós",
            
            # English to French
            ("en", "fr", "Hello"): "Bonjour",
            ("en", "fr", "World"): "Monde",
            ("en", "fr", "Thank you"): "Merci",
            ("en", "fr", "Welcome"): "Bienvenue",
            ("en", "fr", "Goodbye"): "Au revoir",
            
            # English to German
            ("en", "de", "Hello"): "Hallo",
            ("en", "de", "World"): "Welt",
            ("en", "de", "Thank you"): "Danke",
            ("en", "de", "Welcome"): "Willkommen",
            ("en", "de", "Goodbye"): "Auf Wiedersehen",
        }
        
        # Replace known phrases with their mock translations
        result = text
        for (src, tgt, phrase), translation in mock_translations.items():
            if src == source_language and tgt == target_language:
                result = result.replace(phrase, translation)
        
        # Add a prefix to indicate this is a mock translation
        return f"[MOCK TRANSLATION {source_language}->{target_language}] {result}"
    
    def translate_text(
        self, 
        text: str, 
        target_language: str = "en",
        source_language: Optional[str] = None
    ) -> str:
        """
        Translate text to the target language.
        
        Args:
            text: Text to translate
            target_language: Target language code (ISO format, e.g., 'en', 'es')
            source_language: Source language code (if None, will be auto-detected)
            
        Returns:
            Translated text
        """
        if not text:
            return ""
        
        # Detect source language if not provided
        if not source_language:
            source_language = self.detect_language(text)
        
        # Skip translation if source and target are the same
        if source_language == target_language:
            return text
        
        # Use mock translation if enabled
        if self.use_mock:
            return self._mock_translate(text, source_language, target_language)
        
        # Use API-based translation
        if self.use_api:
            return self._translate_with_api(text, source_language, target_language)
        
        # Use local model translation (not implemented in this version)
        return f"[Translation from {source_language} to {target_language} not available]"
    
    def _translate_with_api(
        self, 
        text: str, 
        source_language: str,
        target_language: str
    ) -> str:
        """
        Translate text using an API service (e.g., OpenAI).
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Translated text
        """
        try:
            # Check if API key is set and not empty or commented out
            if not self.api_key or not self.api_key.strip() or self.api_key.strip().startswith('#'):
                return f"[Translation error: API key not found. Please set the OPENAI_API_KEY environment variable.]"
            
            # Project-level API keys (starting with sk-proj-) are now supported by OpenAI
            
            if self.api_key == "your_openai_api_key_here" or "your" in self.api_key.lower():
                return f"[Translation error: Placeholder API key detected. Please update your OPENAI_API_KEY environment variable with a valid API key from https://platform.openai.com/api-keys]"
                
            # Ensure the API key is properly formatted for the Authorization header
            api_key = self.api_key.strip()
            
            # For OpenAI, we use a prompt-based approach
            system_prompt = f"You are a professional translator. Translate the following text from {source_language} to {target_language}. Preserve formatting and maintain the original meaning as closely as possible."
            
            # Define the API endpoint
            api_endpoint = "https://api.openai.com/v1/chat/completions"
            
            try:
                response = requests.post(
                    api_endpoint,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": text}
                        ],
                        "temperature": 0.3  # Lower temperature for more accurate translations
                    },
                    timeout=30  # Add a timeout to prevent hanging requests
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                elif response.status_code == 404:
                    error_msg = f"API endpoint not found: {api_endpoint}. Please check if the OpenAI API URL is correct."
                    print(f"API error: {error_msg}")
                    raise ValueError(error_msg)
                elif response.status_code == 401:
                    error_msg = "Authentication error: Invalid API key or unauthorized access. Please check your OpenAI API key."
                    print(f"API error: {error_msg}")
                    raise ValueError(error_msg)
                elif response.status_code == 429:
                    # Check if it's a quota error
                    response_json = response.json()
                    if response_json.get("error", {}).get("type") == "insufficient_quota":
                        error_msg = "You have exceeded your OpenAI API quota. Please check your billing details at https://platform.openai.com/account/billing or use a different API key."
                        print(f"API error: {error_msg}")
                        raise ValueError(error_msg)
                    else:
                        error_msg = "Rate limit exceeded. Please try again later or reduce the frequency of your requests."
                        print(f"API error: {error_msg}")
                        raise ValueError(error_msg)
                else:
                    error_msg = f"API error: Status {response.status_code}, Response: {response.text}"
                    print(error_msg)
                    raise ValueError(error_msg)
                    
            except requests.exceptions.RequestException as req_err:
                error_msg = f"Request error: {str(req_err)}"
                print(f"API request error: {error_msg}")
                raise ValueError(error_msg)
                
        except Exception as e:
            print(f"Translation API error: {str(e)}")
            return f"[Translation error: {str(e)}]"
    
    def _split_text_into_chunks(self, text: str, max_length: int = 512) -> List[str]:
        """
        Split text into manageable chunks for translation.
        
        Args:
            text: Text to split
            max_length: Maximum chunk length
            
        Returns:
            List of text chunks
        """
        # Simple splitting by sentences to avoid cutting in the middle of a sentence
        sentences = text.replace('\n', ' ').split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def translate_document(
        self, 
        document_id: str, 
        target_language: str = "en",
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate an entire document.
        
        Args:
            document_id: ID of the document to translate
            target_language: Target language code
            source_language: Source language code (if None, will be auto-detected)
            
        Returns:
            Dictionary with translation results
        """
        from core.document.processor import PDFProcessor
        
        # Get document text
        pdf_processor = PDFProcessor(self.base_dir)
        text = pdf_processor.get_document_text(document_id)
        
        if not text:
            return {"error": "No text found in document"}
        
        # Create directory for translations
        doc_translations_dir = self.translations_dir / document_id
        doc_translations_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if translation already exists
        translation_file = doc_translations_dir / f"{target_language}.txt"
        if translation_file.exists():
            with open(translation_file, 'r', encoding='utf-8') as f:
                translated_text = f.read()
                return {
                    "document_id": document_id,
                    "source_language": source_language or self.detect_language(text[:1000]),
                    "target_language": target_language,
                    "translated_text": translated_text,
                    "cached": True
                }
        
        # Detect source language if not provided
        if not source_language:
            # Use the first 1000 characters for language detection
            source_language = self.detect_language(text[:1000])
        
        # Skip translation if source and target are the same
        if source_language == target_language:
            return {
                "document_id": document_id,
                "source_language": source_language,
                "target_language": target_language,
                "translated_text": text,
                "skipped": True
            }
        
        # Translate the document
        translated_text = self.translate_text(text, target_language, source_language)
        
        # Save translation
        with open(translation_file, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        
        return {
            "document_id": document_id,
            "source_language": source_language,
            "target_language": target_language,
            "translated_text": translated_text,
            "cached": False
        }
    
    def translate_document_pages(
        self, 
        document_id: str, 
        target_language: str = "en",
        page_range: Optional[str] = None,
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate specific pages of a document.
        
        Args:
            document_id: ID of the document
            target_language: Target language code
            page_range: Range of pages to translate (e.g., "1,3,5-7")
            source_language: Source language code (if None, will be auto-detected)
            
        Returns:
            Dictionary with translation results by page
        """
        from core.document.processor import PDFProcessor
        from core.extraction.extractor import DataExtractor
        
        # Initialize components
        pdf_processor = PDFProcessor(self.base_dir)
        data_extractor = DataExtractor(self.base_dir)
        
        # Get document metadata
        doc_metadata = pdf_processor.get_document(document_id)
        if not doc_metadata:
            return {"error": "Document not found"}
        
        # Parse page specification
        if page_range:
            page_numbers = data_extractor._parse_page_spec(page_range, doc_metadata.page_count)
        else:
            page_numbers = list(range(doc_metadata.page_count))
        
        # Create directory for translations
        doc_translations_dir = self.translations_dir / document_id
        doc_translations_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract and translate text page by page
        translations = {}
        detected_languages = {}
        
        for page_idx in page_numbers:
            page_num = page_idx + 1  # Convert to 1-based page numbers
            
            # Extract text for this page
            page_text = data_extractor.extract_text(document_id, str(page_num))
            
            if not page_text:
                translations[page_num] = {
                    "error": "No text found on page",
                    "translated_text": ""
                }
                continue
            
            # Check if translation already exists
            page_translation_file = doc_translations_dir / f"page_{page_num}_{target_language}.txt"
            if page_translation_file.exists():
                with open(page_translation_file, 'r', encoding='utf-8') as f:
                    translated_text = f.read()
                    translations[page_num] = {
                        "source_language": source_language or self.detect_language(page_text),
                        "target_language": target_language,
                        "translated_text": translated_text,
                        "cached": True
                    }
                continue
            
            # Detect source language if not provided
            page_source_lang = source_language
            if not page_source_lang:
                page_source_lang = self.detect_language(page_text)
                detected_languages[page_num] = page_source_lang
            
            # Skip translation if source and target are the same
            if page_source_lang == target_language:
                translations[page_num] = {
                    "source_language": page_source_lang,
                    "target_language": target_language,
                    "translated_text": page_text,
                    "skipped": True
                }
                continue
            
            # Translate the page
            translated_text = self.translate_text(page_text, target_language, page_source_lang)
            
            # Save translation
            with open(page_translation_file, 'w', encoding='utf-8') as f:
                f.write(translated_text)
            
            translations[page_num] = {
                "source_language": page_source_lang,
                "target_language": target_language,
                "translated_text": translated_text,
                "cached": False
            }
        
        return {
            "document_id": document_id,
            "target_language": target_language,
            "page_count": len(translations),
            "translations": translations,
            "detected_languages": detected_languages
        }
