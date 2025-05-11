import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional, Dict, Any
import shutil
from pathlib import Path

from utils import validate_pdf, check_pdf_issues

from core.document.processor import PDFProcessor
from core.search.engine import SearchEngine
from core.extraction.extractor import DataExtractor
from core.analytics.analyzer import ContentAnalyzer
from core.translation.translator import TranslationService
from models.document import DocumentMetadata, SearchQuery, SearchResult

# Create FastAPI app
app = FastAPI(
    title="Searchable PDF Library",
    description="An API for processing, searching, and extracting data from PDF documents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create necessary directories if they don't exist
UPLOAD_DIR = Path("storage/uploads")
PROCESSED_DIR = Path("storage/processed")
EXTRACTED_DIR = Path("storage/extracted")

for directory in [UPLOAD_DIR, PROCESSED_DIR, EXTRACTED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Initialize components
pdf_processor = PDFProcessor()
search_engine = SearchEngine()
data_extractor = DataExtractor()
content_analyzer = ContentAnalyzer()
translation_service = TranslationService()

# Mount static files directories
app.mount("/files", StaticFiles(directory="storage"), name="storage")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    # Serve the main HTML page
    with open("static/index.html", "r") as f:
        html_content = f.read()
    return html_content

@app.get("/api")
async def api_root():
    return {"message": "Welcome to the Searchable PDF Library API"}

@app.post("/documents/check")
async def check_document(
    file: UploadFile = File(...)
):
    """
    Check a PDF document for issues before uploading.
    This endpoint allows users to validate their PDFs and get information about potential issues
    without committing to the upload process.
    """
    # Validate file is a PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Create a temporary filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    temp_filename = f"temp_{timestamp}_{file.filename.replace(' ', '_')}"
    temp_path = UPLOAD_DIR / temp_filename
    
    try:
        # Save the uploaded file temporarily
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate the PDF file
        is_valid, error_message = validate_pdf(temp_path)
        if not is_valid:
            return {
                "valid": False,
                "error": error_message,
                "can_process": False,
                "issues": [],
                "warnings": [],
                "info": {}
            }
        
        # Check for potential issues
        pdf_check_result = check_pdf_issues(temp_path)
        
        # Prepare response
        response = {
            "valid": True,
            "can_process": not pdf_check_result["has_issues"],
            "issues": pdf_check_result["issues"],
            "warnings": pdf_check_result["warnings"],
            "info": pdf_check_result["info"]
        }
        
        return response
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error checking PDF: {str(e)}")
        print(f"Traceback: {error_trace}")
        
        return {
            "valid": False,
            "error": str(e),
            "can_process": False,
            "issues": [],
            "warnings": [],
            "info": {}
        }
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection: Optional[str] = Form(None),
    request: Request = None
):
    """
    Upload a PDF document to the library.
    Optionally specify a collection name to organize documents.
    """
    # Validate file is a PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Create a unique filename to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = UPLOAD_DIR / safe_filename
    
    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate the PDF file
        is_valid, error_message = validate_pdf(file_path)
        if not is_valid:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Invalid PDF file: {error_message}")
        
        # Check for potential issues with the PDF
        pdf_check_result = check_pdf_issues(file_path)
        
        # If there are critical issues, reject the file
        if pdf_check_result["has_issues"]:
            os.remove(file_path)
            issues_str = "; ".join(pdf_check_result["issues"])
            raise HTTPException(
                status_code=400, 
                detail=f"PDF has critical issues that prevent processing: {issues_str}"
            )
        
        # Log warnings for potential problems
        if pdf_check_result["warnings"]:
            warnings_str = "; ".join(pdf_check_result["warnings"])
            print(f"Warning for PDF {file.filename}: {warnings_str}")
        
        # Process the PDF
        try:
            metadata = pdf_processor.process(file_path, collection)
            
            # Add any warnings to the response
            metadata_dict = metadata.to_json_dict()
            
            if pdf_check_result["warnings"]:
                metadata_dict["warnings"] = pdf_check_result["warnings"]
            
            return metadata_dict
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error processing PDF: {str(e)}")
            print(f"Traceback: {error_trace}")
            
            # If processing fails, delete the uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Return a more detailed error message
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing PDF: {str(e)}. Please check the file format and try again."
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Unexpected error during upload: {str(e)}")
        print(f"Traceback: {error_trace}")
        
        # Clean up if needed
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@app.get("/documents")
async def list_documents(
    collection: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    List all documents in the library.
    Optionally filter by collection.
    """
    try:
        documents = pdf_processor.list_documents(collection, page, limit)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """
    Get metadata for a specific document.
    """
    try:
        document = pdf_processor.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from the library.
    """
    try:
        success = pdf_processor.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.post("/search")
async def search_documents(query: SearchQuery):
    """
    Search across all documents in the library.
    """
    try:
        results = search_engine.search(
            query.text,
            collection=query.collection,
            metadata_filters=query.metadata_filters,
            page=query.page,
            limit=query.limit
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@app.get("/documents/{document_id}/extract/text")
async def extract_text(
    document_id: str,
    pages: Optional[str] = None  # Format: "1,3,5-7"
):
    """
    Extract text from a document.
    Optionally specify pages to extract from.
    """
    try:
        text = data_extractor.extract_text(document_id, pages)
        return {"document_id": document_id, "text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")

@app.get("/documents/{document_id}/extract/tables")
async def extract_tables(
    document_id: str,
    pages: Optional[str] = None,  # Format: "1,3,5-7"
    format: str = Query("json", regex="^(json|csv|excel)$")
):
    """
    Extract tables from a document.
    Optionally specify pages to extract from and output format.
    """
    try:
        # Check if document exists
        document = pdf_processor.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if document has tables
        if not document.has_tables:
            # This is just a warning, not an error - we'll still try to extract tables
            print(f"Warning: Document {document_id} is not marked as having tables")
        
        try:
            result = data_extractor.extract_tables(document_id, pages, format)
            
            if format == "json":
                return result
            else:
                # For CSV or Excel, return a file
                file_path = EXTRACTED_DIR / f"{document_id}_tables.{format}"
                
                # Check if file exists
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Generated {format} file not found at expected location: {file_path}")
                
                return FileResponse(
                    path=file_path,
                    filename=f"{document_id}_tables.{format}",
                    media_type="application/octet-stream"
                )
        except ImportError as e:
            # Handle missing dependencies
            raise HTTPException(status_code=500, detail=f"Missing dependency: {str(e)}")
        except FileNotFoundError as e:
            # Handle file not found errors
            raise HTTPException(status_code=500, detail=f"File error: {str(e)}")
        except ValueError as e:
            # Handle validation errors
            raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
        except Exception as e:
            # Log the full error with traceback for debugging
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error extracting tables from document {document_id}: {str(e)}")
            print(f"Traceback: {error_trace}")
            
            # Return a more helpful error message
            raise HTTPException(
                status_code=500, 
                detail=f"Error extracting tables: {str(e)}. Please check the document format and try again."
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        import traceback
        error_trace = traceback.format_exc()
        print(f"Unexpected error in extract_tables endpoint: {str(e)}")
        print(f"Traceback: {error_trace}")
        
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/documents/{document_id}/analyze/summary")
async def generate_summary(document_id: str, max_length: int = Query(500, ge=100, le=2000)):
    """
    Generate a summary of the document content.
    """
    try:
        summary = content_analyzer.generate_summary(document_id, max_length)
        return {"document_id": document_id, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@app.get("/documents/{document_id}/analyze/entities")
async def extract_entities(document_id: str):
    """
    Extract named entities from the document.
    """
    try:
        entities = content_analyzer.extract_entities(document_id)
        return {"document_id": document_id, "entities": entities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting entities: {str(e)}")

@app.get("/documents/{document_id}/translate")
async def translate_document(
    document_id: str,
    target_language: str = Query("en", regex="^[a-z]{2}$"),
    source_language: Optional[str] = Query(None, regex="^[a-z]{2}$")
):
    """
    Translate a document to the target language.
    """
    try:
        result = translation_service.translate_document(
            document_id, 
            target_language,
            source_language
        )
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error translating document: {str(e)}")

@app.get("/documents/{document_id}/translate/pages")
async def translate_document_pages(
    document_id: str,
    target_language: str = Query("en", regex="^[a-z]{2}$"),
    pages: Optional[str] = None,
    source_language: Optional[str] = Query(None, regex="^[a-z]{2}$")
):
    """
    Translate specific pages of a document to the target language.
    """
    try:
        result = translation_service.translate_document_pages(
            document_id, 
            target_language,
            pages,
            source_language
        )
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error translating document pages: {str(e)}")

@app.post("/translate/text")
async def translate_text(
    request: Request,
    target_language: str = Query("en", regex="^[a-z]{2}$"),
    source_language: Optional[str] = Query(None, regex="^[a-z]{2}$")
):
    """
    Translate arbitrary text to the target language.
    """
    try:
        data = await request.json()
        text = data.get("text", "")
        
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        translated_text = translation_service.translate_text(
            text,
            target_language,
            source_language
        )
        
        return {
            "source_language": source_language or translation_service.detect_language(text),
            "target_language": target_language,
            "original_text": text,
            "translated_text": translated_text
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error translating text: {str(e)}")

@app.get("/documents/{document_id}/extract/figures")
async def extract_figures(
    document_id: str,
    pages: Optional[str] = None,  # Format: "1,3,5-7"
    format: str = Query("json", regex="^(json|zip)$"),
    image_format: str = Query("jpg", regex="^(jpg|png)$")
):
    """
    Extract figures from a document.
    Optionally specify pages to extract from and output format.
    """
    try:
        # Check if document exists
        document = pdf_processor.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if document has images
        if not document.has_images:
            # This is just a warning, not an error - we'll still try to extract figures
            print(f"Warning: Document {document_id} is not marked as having images")
        
        try:
            result = data_extractor.extract_figures(document_id, pages, format, image_format)
            
            if format == "json":
                return result
            else:
                # For ZIP, return a file
                file_path = EXTRACTED_DIR / f"{document_id}_figures.zip"
                
                # Check if file exists
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Generated ZIP file not found at expected location: {file_path}")
                
                return FileResponse(
                    path=file_path,
                    filename=f"{document_id}_figures.zip",
                    media_type="application/zip"
                )
        except ImportError as e:
            # Handle missing dependencies
            raise HTTPException(status_code=500, detail=f"Missing dependency: {str(e)}")
        except FileNotFoundError as e:
            # Handle file not found errors
            raise HTTPException(status_code=500, detail=f"File error: {str(e)}")
        except ValueError as e:
            # Handle validation errors
            raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
        except Exception as e:
            # Log the full error with traceback for debugging
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error extracting figures from document {document_id}: {str(e)}")
            print(f"Traceback: {error_trace}")
            
            # Return a more helpful error message
            raise HTTPException(
                status_code=500, 
                detail=f"Error extracting figures: {str(e)}. Please check the document format and try again."
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        import traceback
        error_trace = traceback.format_exc()
        print(f"Unexpected error in extract_figures endpoint: {str(e)}")
        print(f"Traceback: {error_trace}")
        
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
