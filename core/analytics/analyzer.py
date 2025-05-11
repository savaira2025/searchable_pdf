import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from collections import Counter

from models.document import Entity, DocumentSummary
from core.document.processor import PDFProcessor
from utils.imports import (
    HAS_NLTK, HAS_SPACY, 
    nltk, spacy,
    optional_import
)

# Conditionally import NLTK components
if HAS_NLTK:
    try:
        from nltk.tokenize import sent_tokenize, word_tokenize
        from nltk.corpus import stopwords
        from nltk.probability import FreqDist
    except ImportError:
        # Fallback simple implementations
        def sent_tokenize(text):
            return text.split('. ')
            
        def word_tokenize(text):
            return text.split()
            
        stopwords = None
        FreqDist = Counter
else:
    # Simple fallback implementations if NLTK is not available
    def sent_tokenize(text):
        return text.split('. ')
        
    def word_tokenize(text):
        return text.split()
        
    stopwords = None
    FreqDist = Counter

class ContentAnalyzer:
    """
    Handles analysis of PDF document content, including:
    - Generating summaries
    - Extracting entities
    - Topic modeling
    - Sentiment analysis
    """
    
    def __init__(self, base_dir: str = "storage"):
        self.base_dir = Path(base_dir)
        self.analytics_dir = self.base_dir / "analytics"
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        
        self.pdf_processor = PDFProcessor(base_dir)
        
        # Initialize NLP components
        self.nlp = None
        
        if HAS_NLTK:
            try:
                # Download NLTK resources if not already downloaded
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
            except Exception as e:
                print(f"Warning: Failed to download NLTK resources: {e}")
        
        if HAS_SPACY:
            try:
                # Load spaCy model if available
                self.nlp = spacy.load("en_core_web_sm")
            except Exception as e:
                print(f"Warning: Failed to load spaCy model: {e}")
    
    def generate_summary(self, document_id: str, max_length: int = 500) -> str:
        """
        Generate a summary of the document content.
        
        Args:
            document_id: ID of the document
            max_length: Maximum length of the summary in characters
            
        Returns:
            Generated summary
        """
        # Get document text
        text = self.pdf_processor.get_document_text(document_id)
        if not text:
            raise ValueError(f"No text found for document: {document_id}")
        
        # Create directory for analytics
        doc_analytics_dir = self.analytics_dir / document_id
        doc_analytics_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if summary already exists
        summary_file = doc_analytics_dir / "summary.txt"
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = f.read()
                if summary:
                    return summary
        
        # Generate summary
        summary = self._extract_summary(text, max_length)
        
        # Save summary
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        # Create summary object
        doc_summary = DocumentSummary(
            document_id=document_id,
            summary=summary
        )
        
        # Save summary metadata
        summary_dict = doc_summary.dict()
        # Convert datetime objects to strings
        summary_dict = self.pdf_processor._convert_datetime_to_str(summary_dict)
        with open(doc_analytics_dir / "summary.json", 'w') as f:
            json.dump(summary_dict, f)
        
        return summary
    
    def extract_entities(self, document_id: str) -> List[Entity]:
        """
        Extract named entities from the document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of extracted entities
        """
        # Get document text
        text = self.pdf_processor.get_document_text(document_id)
        if not text:
            raise ValueError(f"No text found for document: {document_id}")
        
        # Create directory for analytics
        doc_analytics_dir = self.analytics_dir / document_id
        doc_analytics_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if entities already extracted
        entities_file = doc_analytics_dir / "entities.json"
        if entities_file.exists():
            with open(entities_file, 'r') as f:
                entities_data = json.load(f)
                return [Entity(**entity) for entity in entities_data]
        
        # Extract entities
        entities = self._extract_named_entities(text)
        
        # Save entities
        entities_dict = [entity.dict() for entity in entities]
        # Convert datetime objects to strings
        entities_dict = self.pdf_processor._convert_datetime_to_str(entities_dict)
        with open(entities_file, 'w') as f:
            json.dump(entities_dict, f)
        
        return entities
    
    def analyze_sentiment(self, document_id: str) -> Dict[str, Any]:
        """
        Analyze sentiment of the document content.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Dictionary with sentiment analysis results
        """
        # Get document text
        text = self.pdf_processor.get_document_text(document_id)
        if not text:
            raise ValueError(f"No text found for document: {document_id}")
        
        # Create directory for analytics
        doc_analytics_dir = self.analytics_dir / document_id
        doc_analytics_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if sentiment analysis already exists
        sentiment_file = doc_analytics_dir / "sentiment.json"
        if sentiment_file.exists():
            with open(sentiment_file, 'r') as f:
                return json.load(f)
        
        # Analyze sentiment
        # This is a placeholder - for a real implementation, you would use a sentiment analysis library
        sentiment = {
            "overall": "neutral",
            "score": 0.0,
            "positive": 0.0,
            "negative": 0.0,
            "neutral": 1.0
        }
        
        # Save sentiment analysis
        with open(sentiment_file, 'w') as f:
            json.dump(sentiment, f)
        
        return sentiment
    
    def _extract_summary(self, text: str, max_length: int = 500) -> str:
        """
        Extract a summary from text using a simple extractive summarization approach.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of the summary in characters
            
        Returns:
            Generated summary
        """
        # Split text into sentences
        sentences = sent_tokenize(text)
        
        if not sentences:
            return ""
        
        # If text is short, return it as is
        if len(text) <= max_length:
            return text
        
        # Tokenize words and remove stopwords
        word_tokens = word_tokenize(text.lower())
        
        # Remove stopwords if available
        if HAS_NLTK and stopwords:
            try:
                stop_words = set(stopwords.words('english'))
                filtered_words = [word for word in word_tokens if word.isalnum() and word not in stop_words]
            except Exception:
                # Fallback if stopwords not available
                filtered_words = [word for word in word_tokens if word.isalnum()]
        else:
            # Simple stopwords list if NLTK is not available
            simple_stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                               'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'of'}
            filtered_words = [word for word in word_tokens if word.isalnum() and word not in simple_stopwords]
        
        # Calculate word frequencies
        word_freq = FreqDist(filtered_words) if HAS_NLTK else Counter(filtered_words)
        
        # Score sentences based on word frequencies
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            score = 0
            words = word_tokenize(sentence.lower())
            for word in words:
                if word in word_freq:
                    score += word_freq[word]
            sentence_scores[i] = score / max(1, len(words))
        
        # Select top sentences
        top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build summary by adding sentences until max_length is reached
        summary_sentences = []
        current_length = 0
        
        # Always include the first sentence for context
        if sentences:
            summary_sentences.append((0, sentences[0]))
            current_length += len(sentences[0])
        
        # Add top-scoring sentences
        for idx, _ in top_sentences:
            # Skip the first sentence if already included
            if idx == 0:
                continue
                
            sentence = sentences[idx]
            if current_length + len(sentence) + 1 <= max_length:  # +1 for space
                summary_sentences.append((idx, sentence))
                current_length += len(sentence) + 1
            else:
                break
        
        # Sort sentences by their original order
        summary_sentences.sort(key=lambda x: x[0])
        
        # Join sentences
        summary = " ".join(sentence for _, sentence in summary_sentences)
        
        return summary
    
    def _extract_named_entities(self, text: str) -> List[Entity]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        if HAS_SPACY and self.nlp:
            try:
                # Use spaCy for entity extraction
                doc = self.nlp(text)
                
                # Count entities
                entity_counts = Counter()
                entity_pages = {}
                
                for ent in doc.ents:
                    entity_key = (ent.text, ent.label_)
                    entity_counts[entity_key] += 1
                    
                    # For simplicity, we're not tracking page numbers here
                    # In a real implementation, you would need to process the text page by page
                    if entity_key not in entity_pages:
                        entity_pages[entity_key] = []
                
                # Create Entity objects
                for (text, label), count in entity_counts.items():
                    entity = Entity(
                        text=text,
                        label=label,
                        count=count,
                        pages=entity_pages.get((text, label), [])
                    )
                    entities.append(entity)
                    
                return entities
            except Exception as e:
                print(f"Warning: Error using spaCy for entity extraction: {e}")
                # Fall through to the fallback method
        
        # Fallback to a simple regex-based approach
        # This is a very simplified approach and won't be as accurate as using spaCy
        
        # Extract potential entities using regex patterns
        # Example: capitalized words that might be names
        name_pattern = r'\b[A-Z][a-z]+\b'
        names = re.findall(name_pattern, text)
        
        # Count occurrences
        name_counts = Counter(names)
        
        # Create Entity objects
        for name, count in name_counts.most_common(20):  # Limit to top 20
            entity = Entity(
                text=name,
                label="UNKNOWN",  # We can't determine the entity type without NLP
                count=count,
                pages=[]  # We're not tracking page numbers in this simplified approach
            )
            entities.append(entity)
        
        return entities
