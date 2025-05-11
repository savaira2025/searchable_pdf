#!/usr/bin/env python3
"""
Basic usage examples for the Searchable PDF Library.
This script demonstrates how to use the library programmatically.
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document.processor import PDFProcessor
from core.search.engine import SearchEngine
from core.extraction.extractor import DataExtractor
from core.analytics.analyzer import ContentAnalyzer

def main():
    """Demonstrate basic usage of the Searchable PDF Library."""
    # Initialize components
    pdf_processor = PDFProcessor()
    search_engine = SearchEngine()
    data_extractor = DataExtractor()
    content_analyzer = ContentAnalyzer()
    
    # Example PDF file
    example_pdf = Path("examples/sample.pdf")
    
    if not example_pdf.exists():
        print(f"Error: Example PDF file not found: {example_pdf}")
        print("Please place a sample PDF file at examples/sample.pdf")
        return
    
    print("=== Searchable PDF Library Demo ===")
    print()
    
    # Step 1: Process a PDF document
    print("Step 1: Processing PDF document...")
    metadata = pdf_processor.process(example_pdf, collection="examples")
    print(f"Document processed: {metadata.id}")
    print(f"Title: {metadata.title or 'N/A'}")
    print(f"Author: {metadata.author or 'N/A'}")
    print(f"Pages: {metadata.page_count}")
    print()
    
    # Step 2: Index the document for searching
    print("Step 2: Indexing document for searching...")
    indexed = search_engine.index_document(metadata.id)
    print(f"Document indexed: {indexed}")
    print()
    
    # Step 3: Extract text from the document
    print("Step 3: Extracting text from document...")
    text = data_extractor.extract_text(metadata.id)
    print(f"Extracted text (first 200 chars): {text[:200]}...")
    print()
    
    # Step 4: Extract tables from the document
    print("Step 4: Extracting tables from document...")
    try:
        tables = data_extractor.extract_tables(metadata.id, output_format="json")
        print(f"Found {len(tables)} tables in the document")
        if tables:
            print(f"First table has {len(tables[0]['rows'])} rows and {len(tables[0]['headers'])} columns")
    except Exception as e:
        print(f"No tables found in the document: {str(e)}")
    print()
    
    # Step 5: Generate a summary of the document
    print("Step 5: Generating document summary...")
    summary = content_analyzer.generate_summary(metadata.id, max_length=300)
    print(f"Summary: {summary}")
    print()
    
    # Step 6: Extract entities from the document
    print("Step 6: Extracting entities from document...")
    entities = content_analyzer.extract_entities(metadata.id)
    print(f"Found {len(entities)} entities in the document")
    for i, entity in enumerate(entities[:5]):  # Show first 5 entities
        print(f"  - {entity.text} ({entity.label}): {entity.count} occurrences")
    if len(entities) > 5:
        print(f"  ... and {len(entities) - 5} more")
    print()
    
    # Step 7: Search for content in the document
    print("Step 7: Searching for content...")
    search_term = "example"  # Replace with a term likely to be in your sample document
    results = search_engine.search(search_term)
    print(f"Search results for '{search_term}': {results.total_results} matches")
    for item in results.results:
        print(f"  - Document: {item.document_title or item.document_filename}")
        print(f"    Score: {item.score}")
        if item.highlight:
            print(f"    Context: {item.highlight}")
        print()
    
    print("Demo complete!")
    print(f"Document ID for further exploration: {metadata.id}")
    print("You can use this ID with the CLI or API to perform additional operations.")

if __name__ == "__main__":
    main()
