import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import re
from datetime import datetime
import logging

from models.document import SearchResult, SearchResultItem
from core.document.processor import PDFProcessor
from utils.imports import HAS_WHOOSH, whoosh

# Set up logging
logger = logging.getLogger(__name__)

# Import whoosh components if available
if HAS_WHOOSH:
    from whoosh.index import create_in, open_dir, exists_in
    from whoosh.fields import Schema, TEXT, ID, KEYWORD, DATETIME, NUMERIC, BOOLEAN
    from whoosh.qparser import QueryParser, MultifieldParser
    from whoosh.query import Term, And, Or, Not
    from whoosh.highlight import Highlighter, ContextFragmenter

class SearchEngine:
    """
    Handles indexing and searching of PDF documents using Whoosh.
    """
    
    def __init__(self, base_dir: str = "storage"):
        self.base_dir = Path(base_dir)
        self.index_dir = self.base_dir / "index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.pdf_processor = PDFProcessor(base_dir)
        self.index = None
        self.schema = None
        
        if not HAS_WHOOSH:
            logger.warning("Whoosh is not installed. Search functionality will be limited.")
            return
        
        # Define the schema for the search index
        self.schema = Schema(
            id=ID(stored=True, unique=True),
            filename=TEXT(stored=True),
            title=TEXT(stored=True),
            author=TEXT(stored=True),
            content=TEXT(stored=True),
            collection=ID(stored=True),
            upload_date=DATETIME(stored=True),
            creation_date=DATETIME(stored=True),
            page_count=NUMERIC(stored=True),
            has_tables=BOOLEAN(stored=True),
            has_images=BOOLEAN(stored=True)
        )
        
        # Create or open the index
        try:
            if not exists_in(self.index_dir):
                self.index = create_in(self.index_dir, self.schema)
            else:
                self.index = open_dir(self.index_dir)
        except Exception as e:
            logger.error(f"Error initializing search index: {e}")
            self.index = None
    
    def index_document(self, document_id: str) -> bool:
        """
        Index a document for searching.
        
        Args:
            document_id: ID of the document to index
            
        Returns:
            True if indexing was successful, False otherwise
        """
        if not HAS_WHOOSH or self.index is None:
            logger.warning("Search indexing is not available without Whoosh.")
            return False
            
        # Get document metadata
        doc_metadata = self.pdf_processor.get_document(document_id)
        if not doc_metadata:
            return False
        
        # Get document text
        text = self.pdf_processor.get_document_text(document_id)
        if not text:
            return False
        
        try:
            # Open the index for writing
            writer = self.index.writer()
            
            try:
                # Add document to the index
                writer.update_document(
                    id=document_id,
                    filename=doc_metadata.filename,
                    title=doc_metadata.title or "",
                    author=doc_metadata.author or "",
                    content=text,
                    collection=doc_metadata.collection or "",
                    upload_date=doc_metadata.upload_date,
                    creation_date=doc_metadata.creation_date or datetime.now(),
                    page_count=doc_metadata.page_count,
                    has_tables=doc_metadata.has_tables,
                    has_images=doc_metadata.has_images
                )
                
                # Commit the changes
                writer.commit()
                
                # Update document metadata to mark as indexed
                doc_metadata.indexed = True
                self.pdf_processor._save_metadata(doc_metadata)
                
                return True
            except Exception as e:
                # If an error occurs, cancel the changes
                writer.cancel()
                logger.error(f"Error indexing document: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Error creating index writer: {str(e)}")
            return False
    
    def index_all_documents(self) -> Dict[str, Any]:
        """
        Index all unindexed documents in the library.
        
        Returns:
            Dictionary with indexing results
        """
        # Get all documents
        all_docs = self.pdf_processor.list_documents(limit=1000)
        
        # Track indexing results
        results = {
            "total": len(all_docs["documents"]),
            "indexed": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # Index each document
        for doc in all_docs["documents"]:
            if doc.get('indexed', False):
                results["skipped"] += 1
                continue
            
            success = self.index_document(doc['id'])
            if success:
                results["indexed"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    def remove_from_index(self, document_id: str) -> bool:
        """
        Remove a document from the search index.
        
        Args:
            document_id: ID of the document to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if not HAS_WHOOSH or self.index is None:
            logger.warning("Search indexing is not available without Whoosh.")
            return False
            
        try:
            # Open the index for writing
            writer = self.index.writer()
            
            # Remove the document from the index
            writer.delete_by_term('id', document_id)
            
            # Commit the changes
            writer.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error removing document from index: {str(e)}")
            return False
    
    def search(
        self, 
        query_text: str, 
        collection: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        page: int = 1, 
        limit: int = 10
    ) -> SearchResult:
        """
        Search for documents matching the query.
        
        Args:
            query_text: Text to search for
            collection: Optional collection to search within
            metadata_filters: Optional filters for metadata fields
            page: Page number for pagination
            limit: Number of results per page
            
        Returns:
            SearchResult object with search results
        """
        if not HAS_WHOOSH or self.index is None:
            logger.warning("Search functionality is not available without Whoosh.")
            # Return empty search result
            return SearchResult(
                query=query_text,
                total_results=0,
                page=page,
                limit=limit,
                total_pages=0,
                results=[]
            )
            
        try:
            # Prepare search parameters
            searcher = self.index.searcher()
            
            # Create a simpler query parser for just the content field
            parser = QueryParser("content", self.index.schema)
            
            # Parse the query
            try:
                query = parser.parse(query_text)
            except Exception as e:
                logger.error(f"Error parsing query: {str(e)}")
                # Use a simple term query as fallback
                query = Term("content", query_text)
            
            # Apply collection filter if specified
            if collection:
                query = And([query, Term("collection", collection)])
            
            # Apply metadata filters if specified
            if metadata_filters:
                for field, value in metadata_filters.items():
                    if field in self.schema.names():
                        if isinstance(value, dict):
                            # Handle range queries
                            for op, val in value.items():
                                if op == "$gt":
                                    # Greater than
                                    pass  # Implement based on field type
                                elif op == "$lt":
                                    # Less than
                                    pass  # Implement based on field type
                                elif op == "$eq":
                                    # Equal to
                                    query = And([query, Term(field, val)])
                        else:
                            # Simple equality
                            query = And([query, Term(field, value)])
            
            # Calculate pagination
            start_offset = (page - 1) * limit
            
            # Execute the search
            results = searcher.search(query, limit=limit + start_offset)
            
            # Set up highlighter for context
            highlighter = Highlighter(fragmenter=ContextFragmenter(maxchars=200))
            
            # Process results
            total_results = len(results)
            total_pages = (total_results + limit - 1) // limit if total_results > 0 else 1
            
            # Extract paginated results
            paginated_results = results[start_offset:start_offset + limit]
            
            # Format results
            result_items = []
            for hit in paginated_results:
                # Get highlighted content
                if "content" in hit:
                    highlight = highlighter.highlight_hit(hit, "content", query)
                else:
                    highlight = None
                
                # Create result item
                result_item = SearchResultItem(
                    document_id=hit["id"],
                    document_title=hit.get("title", ""),
                    document_filename=hit["filename"],
                    collection=hit.get("collection", ""),
                    page_number=None,  # We don't track which page matched
                    score=hit.score,
                    highlight=highlight
                )
                
                result_items.append(result_item)
            
            # Create search result
            search_result = SearchResult(
                query=query_text,
                total_results=total_results,
                page=page,
                limit=limit,
                total_pages=total_pages,
                results=result_items
            )
            
            # Close the searcher
            searcher.close()
            
            return search_result
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            # Return empty search result on error
            return SearchResult(
                query=query_text,
                total_results=0,
                page=page,
                limit=limit,
                total_pages=0,
                results=[]
            )
    
    def rebuild_index(self) -> Dict[str, Any]:
        """
        Rebuild the entire search index from scratch.
        
        Returns:
            Dictionary with indexing results
        """
        if not HAS_WHOOSH:
            logger.warning("Search indexing is not available without Whoosh.")
            return {
                "total": 0,
                "indexed": 0,
                "failed": 0,
                "skipped": 0,
                "error": "Whoosh is not installed"
            }
            
        try:
            # Delete the existing index
            if self.index_dir.exists():
                shutil.rmtree(self.index_dir)
            
            # Create a new index
            self.index_dir.mkdir(parents=True, exist_ok=True)
            self.index = create_in(self.index_dir, self.schema)
            
            # Reset indexed flag for all documents
            try:
                if os.path.exists(self.pdf_processor.metadata_file):
                    with open(self.pdf_processor.metadata_file, 'r') as f:
                        all_metadata = json.load(f)
                    
                    for doc_id, metadata in all_metadata.items():
                        metadata['indexed'] = False
                    
                    # Convert datetime objects to strings using PDFProcessor's method
                    all_metadata = self.pdf_processor._convert_datetime_to_str(all_metadata)
                    
                    # Save the updated metadata
                    temp_file = self.pdf_processor.metadata_file.with_suffix('.json.tmp')
                    with open(temp_file, 'w') as f:
                        json.dump(all_metadata, f)
                    
                    # Replace the original file with the temporary file
                    temp_file.replace(self.pdf_processor.metadata_file)
            except Exception as e:
                logger.error(f"Error resetting document indexed flags: {str(e)}")
            
            # Index all documents
            return self.index_all_documents()
        except Exception as e:
            logger.error(f"Error rebuilding index: {str(e)}")
            return {
                "total": 0,
                "indexed": 0,
                "failed": 0,
                "skipped": 0,
                "error": str(e)
            }
