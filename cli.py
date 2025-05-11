#!/usr/bin/env python3
"""
Command-line interface for the Searchable PDF Library.
This allows users to interact with the library from the command line.
"""

import os
import sys
import argparse
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

from core.document.processor import PDFProcessor
from core.search.engine import SearchEngine
from core.extraction.extractor import DataExtractor
from core.analytics.analyzer import ContentAnalyzer
from core.translation.translator import TranslationService

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Searchable PDF Library CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload a PDF document")
    upload_parser.add_argument("file", help="Path to the PDF file")
    upload_parser.add_argument("--collection", help="Collection to add the document to")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List documents in the library")
    list_parser.add_argument("--collection", help="Filter by collection")
    list_parser.add_argument("--page", type=int, default=1, help="Page number")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of documents per page")
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get document metadata")
    get_parser.add_argument("id", help="Document ID")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a document")
    delete_parser.add_argument("id", help="Document ID")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--collection", help="Filter by collection")
    search_parser.add_argument("--page", type=int, default=1, help="Page number")
    search_parser.add_argument("--limit", type=int, default=10, help="Number of results per page")
    
    # Extract text command
    extract_text_parser = subparsers.add_parser("extract-text", help="Extract text from a document")
    extract_text_parser.add_argument("id", help="Document ID")
    extract_text_parser.add_argument("--pages", help="Pages to extract (e.g., '1,3,5-7')")
    extract_text_parser.add_argument("--output", help="Output file path")
    
    # Extract tables command
    extract_tables_parser = subparsers.add_parser("extract-tables", help="Extract tables from a document")
    extract_tables_parser.add_argument("id", help="Document ID")
    extract_tables_parser.add_argument("--pages", help="Pages to extract (e.g., '1,3,5-7')")
    extract_tables_parser.add_argument("--format", choices=["json", "csv", "excel"], default="json", help="Output format")
    extract_tables_parser.add_argument("--output", help="Output file path")
    
    # Summarize command
    summarize_parser = subparsers.add_parser("summarize", help="Generate a summary of a document")
    summarize_parser.add_argument("id", help="Document ID")
    summarize_parser.add_argument("--max-length", type=int, default=500, help="Maximum length of the summary")
    summarize_parser.add_argument("--output", help="Output file path")
    
    # Extract entities command
    entities_parser = subparsers.add_parser("entities", help="Extract entities from a document")
    entities_parser.add_argument("id", help="Document ID")
    entities_parser.add_argument("--output", help="Output file path")
    
    # Translate command
    translate_parser = subparsers.add_parser("translate", help="Translate a document to a different language")
    translate_parser.add_argument("id", help="Document ID")
    translate_parser.add_argument("--target-language", default="en", help="Target language code (e.g., 'es' for Spanish)")
    translate_parser.add_argument("--source-language", help="Source language code (auto-detected if not provided)")
    translate_parser.add_argument("--pages", help="Pages to translate (e.g., '1,3,5-7')")
    translate_parser.add_argument("--output", help="Output file path")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Index documents for searching")
    index_parser.add_argument("--rebuild", action="store_true", help="Rebuild the entire index")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize components
    pdf_processor = PDFProcessor()
    search_engine = SearchEngine()
    data_extractor = DataExtractor()
    content_analyzer = ContentAnalyzer()
    translation_service = TranslationService()
    
    # Execute command
    if args.command == "upload":
        upload_document(args, pdf_processor)
    elif args.command == "list":
        list_documents(args, pdf_processor)
    elif args.command == "get":
        get_document(args, pdf_processor)
    elif args.command == "delete":
        delete_document(args, pdf_processor)
    elif args.command == "search":
        search_documents(args, search_engine)
    elif args.command == "extract-text":
        extract_text(args, data_extractor)
    elif args.command == "extract-tables":
        extract_tables(args, data_extractor)
    elif args.command == "summarize":
        summarize_document(args, content_analyzer)
    elif args.command == "entities":
        extract_entities(args, content_analyzer)
    elif args.command == "translate":
        translate_document(args, translation_service)
    elif args.command == "index":
        index_documents(args, search_engine)
    else:
        parser.print_help()

def upload_document(args, pdf_processor):
    """Upload a PDF document to the library."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return
    
    if not file_path.name.lower().endswith('.pdf'):
        print("Error: Only PDF files are accepted")
        return
    
    try:
        metadata = pdf_processor.process(file_path, args.collection)
        print(f"Document uploaded successfully: {metadata.id}")
        print(f"Title: {metadata.title or 'N/A'}")
        print(f"Author: {metadata.author or 'N/A'}")
        print(f"Pages: {metadata.page_count}")
        print(f"Collection: {metadata.collection or 'N/A'}")
    except Exception as e:
        print(f"Error uploading document: {str(e)}")

def list_documents(args, pdf_processor):
    """List documents in the library."""
    try:
        result = pdf_processor.list_documents(args.collection, args.page, args.limit)
        
        print(f"Documents: {result['total']} total, page {result['page']} of {result['total_pages']}")
        print()
        
        for doc in result["documents"]:
            print(f"ID: {doc.id}")
            print(f"Title: {doc.title or 'N/A'}")
            print(f"Filename: {doc.filename}")
            print(f"Pages: {doc.page_count}")
            print(f"Collection: {doc.collection or 'N/A'}")
            print(f"Upload Date: {doc.upload_date}")
            print()
    except Exception as e:
        print(f"Error listing documents: {str(e)}")

def get_document(args, pdf_processor):
    """Get document metadata."""
    try:
        doc = pdf_processor.get_document(args.id)
        
        if not doc:
            print(f"Document not found: {args.id}")
            return
        
        print(f"ID: {doc.id}")
        print(f"Title: {doc.title or 'N/A'}")
        print(f"Author: {doc.author or 'N/A'}")
        print(f"Filename: {doc.filename}")
        print(f"Pages: {doc.page_count}")
        print(f"File Size: {doc.file_size} bytes")
        print(f"Collection: {doc.collection or 'N/A'}")
        print(f"Upload Date: {doc.upload_date}")
        print(f"Creation Date: {doc.creation_date or 'N/A'}")
        print(f"Modification Date: {doc.modification_date or 'N/A'}")
        print(f"Processed: {doc.processed}")
        print(f"Indexed: {doc.indexed}")
        print(f"Has Text: {doc.has_text}")
        print(f"Has Tables: {doc.has_tables}")
        print(f"Has Images: {doc.has_images}")
        print(f"Path: {doc.path}")
        print(f"Text Path: {doc.text_path or 'N/A'}")
    except Exception as e:
        print(f"Error getting document: {str(e)}")

def delete_document(args, pdf_processor):
    """Delete a document from the library."""
    try:
        success = pdf_processor.delete_document(args.id)
        
        if success:
            print(f"Document deleted successfully: {args.id}")
        else:
            print(f"Document not found: {args.id}")
    except Exception as e:
        print(f"Error deleting document: {str(e)}")

def search_documents(args, search_engine):
    """Search for documents."""
    try:
        result = search_engine.search(args.query, args.collection, None, args.page, args.limit)
        
        print(f"Search results for '{result.query}': {result.total_results} total, page {result.page} of {result.total_pages}")
        print()
        
        for item in result.results:
            print(f"Document: {item.document_title or item.document_filename}")
            print(f"ID: {item.document_id}")
            print(f"Collection: {item.collection or 'N/A'}")
            print(f"Score: {item.score}")
            
            if item.highlight:
                print(f"Context: {item.highlight}")
            
            print()
    except Exception as e:
        print(f"Error searching documents: {str(e)}")

def extract_text(args, data_extractor):
    """Extract text from a document."""
    try:
        text = data_extractor.extract_text(args.id, args.pages)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Text extracted and saved to {args.output}")
        else:
            print(text)
    except Exception as e:
        print(f"Error extracting text: {str(e)}")

def extract_tables(args, data_extractor):
    """Extract tables from a document."""
    try:
        result = data_extractor.extract_tables(args.id, args.pages, args.format)
        
        if args.format == "json":
            if args.output:
                # Convert result to handle datetime objects
                result = data_extractor.pdf_processor._convert_datetime_to_str(result)
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"Tables extracted and saved to {args.output}")
            else:
                # Convert result to handle datetime objects
                result = data_extractor.pdf_processor._convert_datetime_to_str(result)
                print(json.dumps(result, indent=2))
        else:
            # For CSV and Excel, result is a file path
            if args.output:
                shutil.copy2(result, args.output)
                print(f"Tables extracted and saved to {args.output}")
            else:
                print(f"Tables extracted and saved to {result}")
    except Exception as e:
        print(f"Error extracting tables: {str(e)}")

def summarize_document(args, content_analyzer):
    """Generate a summary of a document."""
    try:
        summary = content_analyzer.generate_summary(args.id, args.max_length)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"Summary generated and saved to {args.output}")
        else:
            print(summary)
    except Exception as e:
        print(f"Error generating summary: {str(e)}")

def extract_entities(args, content_analyzer):
    """Extract entities from a document."""
    try:
        entities = content_analyzer.extract_entities(args.id)
        
        if args.output:
            # Convert entities to dict and handle datetime objects
            entities_dict = [entity.dict() for entity in entities]
            entities_dict = content_analyzer.pdf_processor._convert_datetime_to_str(entities_dict)
            with open(args.output, 'w') as f:
                json.dump(entities_dict, f, indent=2)
            print(f"Entities extracted and saved to {args.output}")
        else:
            for entity in entities:
                print(f"{entity.text} ({entity.label}): {entity.count} occurrences")
    except Exception as e:
        print(f"Error extracting entities: {str(e)}")

def translate_document(args, translation_service):
    """Translate a document to a different language."""
    try:
        if args.pages:
            # Translate specific pages
            result = translation_service.translate_document_pages(
                args.id, 
                args.target_language,
                args.pages,
                args.source_language
            )
            
            if "error" in result:
                print(f"Error: {result['error']}")
                return
            
            print(f"Translated {result['page_count']} pages to {result['target_language']}")
            
            if args.output:
                # Combine all page translations
                all_text = []
                for page_num, translation in sorted(result["translations"].items()):
                    all_text.append(f"--- Page {page_num} ---\n{translation['translated_text']}")
                
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write("\n\n".join(all_text))
                print(f"Translation saved to {args.output}")
            else:
                # Print a preview of each page
                for page_num, translation in sorted(result["translations"].items()):
                    source_lang = translation.get("source_language", "unknown")
                    print(f"\nPage {page_num} (from {source_lang} to {result['target_language']}):")
                    
                    if translation.get("cached", False):
                        print("(Loaded from cache)")
                    elif translation.get("skipped", False):
                        print("(Translation skipped - already in target language)")
                    
                    # Print a preview
                    preview_length = 100
                    text = translation["translated_text"]
                    preview = text[:preview_length] + ("..." if len(text) > preview_length else "")
                    print(preview)
        else:
            # Translate entire document
            result = translation_service.translate_document(
                args.id, 
                args.target_language,
                args.source_language
            )
            
            if "error" in result:
                print(f"Error: {result['error']}")
                return
            
            print(f"Document translated from {result['source_language']} to {result['target_language']}")
            
            if result.get("cached", False):
                print("(Translation loaded from cache)")
            elif result.get("skipped", False):
                print("(Translation skipped - document already in target language)")
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(result["translated_text"])
                print(f"Translation saved to {args.output}")
            else:
                # Print a preview
                preview_length = 500
                text = result["translated_text"]
                preview = text[:preview_length] + ("..." if len(text) > preview_length else "")
                print("\nPreview:")
                print(preview)
    except Exception as e:
        print(f"Error translating document: {str(e)}")

def index_documents(args, search_engine):
    """Index documents for searching."""
    try:
        if args.rebuild:
            print("Rebuilding search index...")
            result = search_engine.rebuild_index()
        else:
            print("Indexing documents...")
            result = search_engine.index_all_documents()
        
        print(f"Indexing complete: {result['indexed']} indexed, {result['skipped']} skipped, {result['failed']} failed")
    except Exception as e:
        print(f"Error indexing documents: {str(e)}")

if __name__ == "__main__":
    main()
