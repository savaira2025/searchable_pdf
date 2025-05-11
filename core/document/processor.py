import os
import shutil
import json
import pdfplumber
import PyPDF2
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import uuid

from models.document import DocumentMetadata, PageInfo
from utils import validate_pdf

# Custom JSON encoder that can handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class PDFProcessor:
    """
    Handles the processing of PDF documents, including:
    - Extracting metadata
    - Extracting text content
    - Analyzing document structure
    - Managing document storage
    """
    
    def __init__(self, base_dir: str = "storage"):
        self.base_dir = Path(base_dir)
        self.uploads_dir = self.base_dir / "uploads"
        self.processed_dir = self.base_dir / "processed"
        self.metadata_file = self.base_dir / "metadata.json"
        
        # Create directories if they don't exist
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metadata storage
        if not self.metadata_file.exists():
            with open(self.metadata_file, 'w') as f:
                json.dump({}, f)
    
    def process(self, file_path: Path, collection: Optional[str] = None) -> DocumentMetadata:
        """
        Process a PDF file and extract its metadata and content.
        
        Args:
            file_path: Path to the PDF file
            collection: Optional collection name to organize documents
            
        Returns:
            DocumentMetadata object with extracted information
        """
        # Validate file path
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
        
        # Validate PDF file
        is_valid, error_message = validate_pdf(file_path)
        if not is_valid:
            raise ValueError(f"Invalid PDF file: {error_message}")
            
        try:
            # Generate a unique ID for the document
            doc_id = str(uuid.uuid4())
            
            # Create a directory for processed files
            doc_dir = self.processed_dir / doc_id
            doc_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract basic file information
            try:
                file_size = file_path.stat().st_size
                filename = file_path.name
            except Exception as e:
                raise IOError(f"Error accessing file information: {str(e)}")
            
            # Extract PDF metadata and content
            try:
                metadata, pages_info = self._extract_pdf_info(file_path)
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"Error extracting PDF information: {str(e)}")
                print(f"Traceback: {error_trace}")
                raise ValueError(f"Failed to extract PDF information: {str(e)}")
            
            # Save extracted text to a file
            text_path = doc_dir / "text.txt"
            try:
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(metadata.get('text', ''))
            except Exception as e:
                raise IOError(f"Error saving extracted text: {str(e)}")
            
            # Create document metadata
            try:
                doc_metadata = DocumentMetadata(
                    id=doc_id,
                    filename=filename,
                    title=metadata.get('title'),
                    author=metadata.get('author'),
                    creation_date=metadata.get('creation_date'),
                    modification_date=metadata.get('modification_date'),
                    page_count=metadata.get('page_count', 0),
                    file_size=file_size,
                    collection=collection,
                    upload_date=datetime.now(),
                    processed=True,
                    indexed=False,  # Will be indexed by the search engine later
                    has_text=bool(metadata.get('text')),
                    has_tables=metadata.get('has_tables', False),
                    has_images=metadata.get('has_images', False),
                    path=str(file_path),
                    text_path=str(text_path)
                )
            except Exception as e:
                raise ValueError(f"Error creating document metadata: {str(e)}")
            
            # Save page information
            try:
                # Convert page info to dict and handle datetime objects
                pages_dict = [page.dict() for page in pages_info]
                pages_dict = self._convert_datetime_to_str(pages_dict)
                with open(doc_dir / "pages.json", 'w') as f:
                    json.dump(pages_dict, f)
            except Exception as e:
                raise IOError(f"Error saving page information: {str(e)}")
            
            # Save document metadata
            try:
                self._save_metadata(doc_metadata)
            except Exception as e:
                raise IOError(f"Error saving document metadata: {str(e)}")
            
            # Copy the original file to the processed directory
            try:
                shutil.copy2(file_path, doc_dir / filename)
            except Exception as e:
                raise IOError(f"Error copying original file: {str(e)}")
            
            # Convert to dict and handle datetime objects for JSON serialization
            document_dict = doc_metadata.dict()
            document_dict = self._convert_datetime_to_str(document_dict)
            return DocumentMetadata(**document_dict)
            
        except Exception as e:
            # Clean up any created directories if processing fails
            try:
                if 'doc_dir' in locals() and doc_dir.exists():
                    shutil.rmtree(doc_dir)
            except:
                pass
            
            # Re-raise the exception with more context
            raise ValueError(f"Failed to process PDF: {str(e)}")
    
    def _extract_pdf_info(self, file_path: Path) -> Tuple[Dict[str, Any], List[PageInfo]]:
        """
        Extract information from a PDF file using pdfplumber and PyPDF2.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple containing:
                - Dictionary with metadata and extracted text
                - List of PageInfo objects with page-specific information
        """
        metadata = {}
        pages_info = []
        full_text = []
        has_tables = False
        has_images = False
        
        # Extract metadata using PyPDF2
        try:
            with open(file_path, 'rb') as f:
                try:
                    pdf_reader = PyPDF2.PdfReader(f)
                    
                    # Basic metadata
                    metadata['page_count'] = len(pdf_reader.pages)
                    
                    # PDF document info
                    if pdf_reader.metadata:
                        info = pdf_reader.metadata
                        metadata['title'] = info.get('/Title')
                        metadata['author'] = info.get('/Author')
                        
                        # Try to parse dates
                        try:
                            if info.get('/CreationDate'):
                                # PDF dates are in format: D:YYYYMMDDHHmmSS
                                date_str = info.get('/CreationDate')
                                if date_str.startswith('D:'):
                                    date_str = date_str[2:]
                                    metadata['creation_date'] = datetime.strptime(date_str[:14], '%Y%m%d%H%M%S')
                        except Exception as e:
                            print(f"Warning: Could not parse creation date: {str(e)}")
                        
                        try:
                            if info.get('/ModDate'):
                                date_str = info.get('/ModDate')
                                if date_str.startswith('D:'):
                                    date_str = date_str[2:]
                                    metadata['modification_date'] = datetime.strptime(date_str[:14], '%Y%m%d%H%M%S')
                        except Exception as e:
                            print(f"Warning: Could not parse modification date: {str(e)}")
                except Exception as e:
                    raise ValueError(f"Error reading PDF with PyPDF2: {str(e)}. The file may be corrupted or password-protected.")
        except Exception as e:
            raise IOError(f"Error opening PDF file: {str(e)}")
        
        # Extract text and analyze structure using pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    try:
                        # Extract page dimensions
                        page_info = PageInfo(
                            page_number=i + 1,
                            width=float(page.width),
                            height=float(page.height),
                            has_text=True,  # Default assumption
                            has_tables=False,
                            has_images=False,
                            word_count=0
                        )
                        
                        # Extract text
                        try:
                            text = page.extract_text() or ""
                            if text:
                                full_text.append(text)
                                page_info.word_count = len(text.split())
                            else:
                                page_info.has_text = False
                        except Exception as e:
                            print(f"Warning: Error extracting text from page {i+1}: {str(e)}")
                            page_info.has_text = False
                        
                        # Check for tables
                        try:
                            tables = page.find_tables()
                            if tables:
                                page_info.has_tables = True
                                has_tables = True
                        except Exception as e:
                            print(f"Warning: Error finding tables on page {i+1}: {str(e)}")
                        
                        # Check for images
                        try:
                            if page.images:
                                page_info.has_images = True
                                has_images = True
                        except Exception as e:
                            print(f"Warning: Error checking for images on page {i+1}: {str(e)}")
                        
                        pages_info.append(page_info)
                    except Exception as e:
                        print(f"Warning: Error processing page {i+1}: {str(e)}")
                        # Add a minimal page info object to maintain page count
                        pages_info.append(PageInfo(
                            page_number=i + 1,
                            width=0,
                            height=0,
                            has_text=False,
                            has_tables=False,
                            has_images=False,
                            word_count=0
                        ))
        except Exception as e:
            # If pdfplumber fails completely, try to provide at least basic metadata
            if 'page_count' not in metadata:
                metadata['page_count'] = 0
            
            # Create empty pages_info if needed
            if not pages_info and metadata['page_count'] > 0:
                for i in range(metadata['page_count']):
                    pages_info.append(PageInfo(
                        page_number=i + 1,
                        width=0,
                        height=0,
                        has_text=False,
                        has_tables=False,
                        has_images=False,
                        word_count=0
                    ))
            
            raise ValueError(f"Error extracting content with pdfplumber: {str(e)}. The PDF may be damaged, encrypted, or contain unsupported features.")
        
        # Combine all extracted text
        metadata['text'] = "\n\n".join(full_text)
        metadata['has_tables'] = has_tables
        metadata['has_images'] = has_images
        
        # Validate the extracted data
        if metadata['page_count'] == 0 or not pages_info:
            raise ValueError("Failed to extract any pages from the PDF. The file may be empty or corrupted.")
        
        if not metadata['text'] and metadata['page_count'] > 0:
            print("Warning: No text was extracted from the PDF. The document may be scanned or contain only images.")
        
        return metadata, pages_info
    
    def _convert_datetime_to_str(self, obj):
        """
        Recursively convert datetime objects to ISO format strings in a dictionary.
        
        Args:
            obj: Object to convert (can be a dict, list, or any other type)
            
        Returns:
            Object with datetime objects converted to strings
        """
        if isinstance(obj, dict):
            return {k: self._convert_datetime_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_datetime_to_str(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj
    
    def _save_metadata(self, metadata: DocumentMetadata) -> None:
        """
        Save document metadata to the metadata storage.
        
        Args:
            metadata: DocumentMetadata object to save
        """
        try:
            # Check if metadata file exists
            if not self.metadata_file.exists():
                print(f"Warning: Metadata file not found at {self.metadata_file}. Creating a new one.")
                all_metadata = {}
            else:
                # Load existing metadata
                try:
                    with open(self.metadata_file, 'r') as f:
                        all_metadata = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Error: Metadata file is corrupted: {str(e)}")
                    
                    # Create a backup of the corrupted file
                    backup_path = self.metadata_file.with_suffix('.json.bak')
                    try:
                        shutil.copy2(self.metadata_file, backup_path)
                        print(f"Created backup of corrupted metadata file at {backup_path}")
                    except Exception as backup_error:
                        print(f"Warning: Failed to create backup of corrupted metadata file: {str(backup_error)}")
                    
                    # Start with a fresh metadata dictionary
                    all_metadata = {}
                except Exception as e:
                    print(f"Error loading metadata file: {str(e)}")
                    all_metadata = {}
            
            # Add or update metadata for this document
            try:
                # Use the to_json_dict method to get a JSON-serializable dictionary
                metadata_dict = metadata.to_json_dict()
                all_metadata[metadata.id] = metadata_dict
            except Exception as e:
                print(f"Error converting metadata to dictionary: {str(e)}")
                # Try a more basic approach
                try:
                    metadata_dict = {
                        "id": metadata.id,
                        "filename": metadata.filename,
                        "title": metadata.title,
                        "author": metadata.author,
                        "page_count": metadata.page_count,
                        "file_size": metadata.file_size,
                        "collection": metadata.collection,
                        "upload_date": metadata.upload_date.isoformat() if metadata.upload_date else None,
                        "processed": metadata.processed,
                        "indexed": metadata.indexed,
                        "has_text": metadata.has_text,
                        "has_tables": metadata.has_tables,
                        "has_images": metadata.has_images,
                        "path": metadata.path,
                        "text_path": metadata.text_path
                    }
                    all_metadata[metadata.id] = metadata_dict
                except Exception as e2:
                    print(f"Error creating basic metadata dictionary: {str(e2)}")
                    raise
            
            # Save updated metadata
            try:
                # Create a temporary file first to avoid corrupting the metadata file
                temp_file = self.metadata_file.with_suffix('.json.tmp')
                with open(temp_file, 'w') as f:
                    # Use the custom JSON encoder to handle datetime objects
                    json.dump(all_metadata, f, cls=DateTimeEncoder)
                
                # Replace the original file with the temporary file
                temp_file.replace(self.metadata_file)
            except Exception as e:
                print(f"Error saving metadata file: {str(e)}")
                
                # Try a direct approach as a fallback
                try:
                    with open(self.metadata_file, 'w') as f:
                        # Use the custom JSON encoder to handle datetime objects
                        json.dump(all_metadata, f, cls=DateTimeEncoder)
                except Exception as e2:
                    print(f"Error saving metadata file (fallback attempt): {str(e2)}")
                    raise
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error saving metadata for document {metadata.id}: {str(e)}")
            print(f"Traceback: {error_trace}")
            raise
    
    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        """
        Get metadata for a specific document.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            DocumentMetadata object if found, None otherwise
        """
        try:
            # Check if metadata file exists
            if not self.metadata_file.exists():
                print(f"Warning: Metadata file not found at {self.metadata_file}")
                return None
            
            # Load metadata
            try:
                with open(self.metadata_file, 'r') as f:
                    all_metadata = json.load(f)
            except json.JSONDecodeError as e:
                # Handle corrupted JSON file
                print(f"Error: Metadata file is corrupted: {str(e)}")
                return None
            
            # Get metadata for the specified document
            doc_metadata = all_metadata.get(document_id)
            if not doc_metadata:
                return None
            
            # Create DocumentMetadata object
            try:
                document = DocumentMetadata(**doc_metadata)
                # Convert to dict and handle datetime objects for JSON serialization
                document_dict = document.dict()
                document_dict = self._convert_datetime_to_str(document_dict)
                return DocumentMetadata(**document_dict)
            except Exception as e:
                print(f"Error creating DocumentMetadata object for document {document_id}: {str(e)}")
                return None
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error retrieving document {document_id}: {str(e)}")
            print(f"Traceback: {error_trace}")
            return None
    
    def list_documents(self, collection: Optional[str] = None, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """
        List documents in the library, optionally filtered by collection.
        
        Args:
            collection: Optional collection name to filter by
            page: Page number for pagination
            limit: Number of documents per page
            
        Returns:
            Dictionary with pagination info and list of documents
        """
        try:
            # Check if metadata file exists
            if not self.metadata_file.exists():
                print(f"Warning: Metadata file not found at {self.metadata_file}. Creating a new one.")
                with open(self.metadata_file, 'w') as f:
                    json.dump({}, f)
                return {
                    "total": 0,
                    "page": page,
                    "limit": limit,
                    "total_pages": 0,
                    "documents": []
                }
            
            # Load metadata
            try:
                with open(self.metadata_file, 'r') as f:
                    all_metadata = json.load(f)
            except json.JSONDecodeError as e:
                # Handle corrupted JSON file
                import traceback
                error_trace = traceback.format_exc()
                print(f"Error: Metadata file is corrupted: {str(e)}")
                print(f"Traceback: {error_trace}")
                
                # Create a backup of the corrupted file
                backup_path = self.metadata_file.with_suffix('.json.bak')
                try:
                    shutil.copy2(self.metadata_file, backup_path)
                    print(f"Created backup of corrupted metadata file at {backup_path}")
                except Exception as backup_error:
                    print(f"Warning: Failed to create backup of corrupted metadata file: {str(backup_error)}")
                
                # Create a new empty metadata file
                with open(self.metadata_file, 'w') as f:
                    json.dump({}, f)
                
                # Return empty results
                return {
                    "total": 0,
                    "page": page,
                    "limit": limit,
                    "total_pages": 0,
                    "documents": []
                }
            
            # Filter by collection if specified
            try:
                if collection:
                    filtered_docs = [
                        doc for doc in all_metadata.values()
                        if doc.get('collection') == collection
                    ]
                else:
                    filtered_docs = list(all_metadata.values())
            except Exception as e:
                print(f"Error filtering documents: {str(e)}")
                filtered_docs = []
            
            # Sort by upload date (newest first)
            try:
                filtered_docs.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
            except Exception as e:
                print(f"Error sorting documents: {str(e)}")
            
            # Paginate results
            total_docs = len(filtered_docs)
            total_pages = max(1, (total_docs + limit - 1) // limit)  # Ceiling division, minimum 1 page
            start_idx = (page - 1) * limit
            end_idx = min(start_idx + limit, total_docs)
            
            # Handle invalid page number
            if start_idx >= total_docs and total_docs > 0:
                # If requested page is beyond available pages, return the last page
                page = total_pages
                start_idx = (page - 1) * limit
                end_idx = min(start_idx + limit, total_docs)
            
            paginated_docs = filtered_docs[start_idx:end_idx]
            
            # Convert to DocumentMetadata objects
            documents = []
            for doc in paginated_docs:
                try:
                    documents.append(DocumentMetadata(**doc))
                except Exception as e:
                    print(f"Error creating DocumentMetadata object: {str(e)}")
                    # Skip invalid documents
                    continue
            
            # Convert response to dict and handle datetime objects
            response = {
                "total": total_docs,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "documents": [doc.dict() for doc in documents]
            }
            response = self._convert_datetime_to_str(response)
            return response
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error listing documents: {str(e)}")
            print(f"Traceback: {error_trace}")
            
            # Return empty results in case of error
            return {
                "total": 0,
                "page": page,
                "limit": limit,
                "total_pages": 0,
                "documents": [],
                "error": str(e)
            }
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the library.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if the document was deleted, False otherwise
        """
        try:
            # Check if metadata file exists
            if not self.metadata_file.exists():
                print(f"Warning: Metadata file not found at {self.metadata_file}")
                return False
            
            # Load metadata
            try:
                with open(self.metadata_file, 'r') as f:
                    all_metadata = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error: Metadata file is corrupted: {str(e)}")
                return False
            
            # Check if document exists
            if document_id not in all_metadata:
                return False
            
            # Get document metadata
            doc_metadata = all_metadata[document_id]
            
            # Delete processed files
            try:
                doc_dir = self.processed_dir / document_id
                if doc_dir.exists():
                    shutil.rmtree(doc_dir)
            except Exception as e:
                print(f"Warning: Error deleting processed files for document {document_id}: {str(e)}")
                # Continue with deletion even if we can't delete the files
            
            # Delete original file if it still exists
            try:
                original_path = Path(doc_metadata.get('path', ''))
                if original_path.exists():
                    original_path.unlink()
            except Exception as e:
                print(f"Warning: Error deleting original file for document {document_id}: {str(e)}")
                # Continue with deletion even if we can't delete the original file
            
            # Remove from metadata
            del all_metadata[document_id]
            
            # Save updated metadata
            try:
                with open(self.metadata_file, 'w') as f:
                    # Use the custom JSON encoder to handle datetime objects
                    json.dump(all_metadata, f, cls=DateTimeEncoder)
            except Exception as e:
                print(f"Error saving metadata after deleting document {document_id}: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error deleting document {document_id}: {str(e)}")
            print(f"Traceback: {error_trace}")
            return False
    
    def get_document_text(self, document_id: str) -> Optional[str]:
        """
        Get the extracted text for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Extracted text if available, None otherwise
        """
        try:
            # Get document metadata
            doc_metadata = self.get_document(document_id)
            if not doc_metadata or not doc_metadata.text_path:
                return None
            
            # Read text file
            text_path = Path(doc_metadata.text_path)
            if not text_path.exists():
                print(f"Warning: Text file not found for document {document_id}: {text_path}")
                return None
            
            try:
                with open(text_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # Try with a different encoding if UTF-8 fails
                try:
                    with open(text_path, 'r', encoding='latin-1') as f:
                        return f.read()
                except Exception as e:
                    print(f"Error reading text file with alternative encoding: {str(e)}")
                    return None
            except Exception as e:
                print(f"Error reading text file: {str(e)}")
                return None
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error retrieving text for document {document_id}: {str(e)}")
            print(f"Traceback: {error_trace}")
            return None
    
    def get_document_pages(self, document_id: str) -> Optional[List[PageInfo]]:
        """
        Get information about the pages in a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of PageInfo objects if available, None otherwise
        """
        try:
            # Check if document exists
            doc_dir = self.processed_dir / document_id
            pages_file = doc_dir / "pages.json"
            
            if not doc_dir.exists():
                print(f"Warning: Document directory not found for document {document_id}: {doc_dir}")
                return None
                
            if not pages_file.exists():
                print(f"Warning: Pages file not found for document {document_id}: {pages_file}")
                return None
            
            # Read pages info
            try:
                with open(pages_file, 'r') as f:
                    pages_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error: Pages file is corrupted for document {document_id}: {str(e)}")
                return None
            
            # Convert to PageInfo objects
            pages = []
            for page_data in pages_data:
                try:
                    pages.append(PageInfo(**page_data))
                except Exception as e:
                    print(f"Error creating PageInfo object: {str(e)}")
                    # Skip invalid pages
                    continue
            
            # Convert page objects to dicts and handle datetime objects for JSON serialization
            pages_dict = [page.dict() for page in pages]
            pages_dict = self._convert_datetime_to_str(pages_dict)
            
            # Convert back to PageInfo objects
            result_pages = []
            for page_data in pages_dict:
                try:
                    result_pages.append(PageInfo(**page_data))
                except Exception as e:
                    print(f"Error creating PageInfo object: {str(e)}")
                    # Skip invalid pages
                    continue
            
            return result_pages
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error retrieving pages for document {document_id}: {str(e)}")
            print(f"Traceback: {error_trace}")
            return None
