#!/usr/bin/env python3
"""
Script to rebuild the metadata.json file from processed documents.
This script scans the storage/processed directory, extracts metadata from each document,
and rebuilds the metadata.json file.
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
import uuid

def rebuild_metadata():
    """Rebuild the metadata.json file from processed documents."""
    print("Starting metadata rebuild process...")
    
    # Define paths
    base_dir = Path("storage")
    processed_dir = base_dir / "processed"
    metadata_file = base_dir / "metadata.json"
    
    # Check if processed directory exists
    if not processed_dir.exists():
        print(f"Error: Processed directory not found at {processed_dir}")
        return False
    
    # Create a backup of the existing metadata file if it exists
    if metadata_file.exists():
        backup_path = metadata_file.with_suffix('.json.bak')
        try:
            shutil.copy2(metadata_file, backup_path)
            print(f"Created backup of existing metadata file at {backup_path}")
        except Exception as e:
            print(f"Warning: Failed to create backup of metadata file: {str(e)}")
    
    # Initialize metadata dictionary
    all_metadata = {}
    
    # Scan processed directory
    document_count = 0
    for doc_dir in processed_dir.iterdir():
        if not doc_dir.is_dir():
            continue
        
        document_id = doc_dir.name
        print(f"Processing document: {document_id}")
        
        try:
            # Check for pages.json
            pages_file = doc_dir / "pages.json"
            if not pages_file.exists():
                print(f"Warning: pages.json not found for document {document_id}, skipping")
                continue
            
            # Read pages.json
            with open(pages_file, 'r') as f:
                pages_data = json.load(f)
            
            # Check for text.txt
            text_file = doc_dir / "text.txt"
            has_text = text_file.exists()
            
            # Find the original PDF file
            pdf_files = list(doc_dir.glob("*.pdf"))
            if not pdf_files:
                print(f"Warning: No PDF file found for document {document_id}")
                filename = f"unknown_{document_id}.pdf"
                file_size = 0
            else:
                filename = pdf_files[0].name
                file_size = pdf_files[0].stat().st_size
            
            # Extract metadata from pages data
            page_count = len(pages_data)
            has_tables = any(page.get('has_tables', False) for page in pages_data)
            has_images = any(page.get('has_images', False) for page in pages_data)
            
            # Create metadata entry
            metadata = {
                "id": document_id,
                "filename": filename,
                "title": filename,  # Use filename as title if not available
                "author": None,  # Not available from pages.json
                "creation_date": None,  # Not available from pages.json
                "modification_date": None,  # Not available from pages.json
                "page_count": page_count,
                "file_size": file_size,
                "collection": None,  # Not available from pages.json
                "upload_date": datetime.now().isoformat(),  # Use current time as upload date
                "processed": True,
                "indexed": False,
                "has_text": has_text,
                "has_tables": has_tables,
                "has_images": has_images,
                "path": str(doc_dir / filename),
                "text_path": str(text_file) if has_text else None
            }
            
            # Add metadata to dictionary
            all_metadata[document_id] = metadata
            document_count += 1
            
        except Exception as e:
            print(f"Error processing document {document_id}: {str(e)}")
            continue
    
    # Write metadata to file
    try:
        with open(metadata_file, 'w') as f:
            json.dump(all_metadata, f, indent=2)
        print(f"Successfully rebuilt metadata for {document_count} documents")
        return True
    except Exception as e:
        print(f"Error writing metadata file: {str(e)}")
        return False

if __name__ == "__main__":
    success = rebuild_metadata()
    if success:
        print("Metadata rebuild completed successfully")
    else:
        print("Metadata rebuild failed")
