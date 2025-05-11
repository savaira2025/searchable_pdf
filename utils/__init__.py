import os
import io
from pathlib import Path
from typing import Tuple, Optional, Dict, List, Any

def validate_pdf(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate if a file is a valid PDF.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        Tuple containing:
            - Boolean indicating if the file is a valid PDF
            - Error message if validation fails, None otherwise
    """
    # Check if file exists
    if not file_path.exists():
        return False, f"File does not exist: {file_path}"
    
    # Check if it's a file
    if not file_path.is_file():
        return False, f"Path is not a file: {file_path}"
    
    # Check file size
    try:
        file_size = file_path.stat().st_size
        if file_size == 0:
            return False, "File is empty"
        if file_size < 4:  # Minimum size for a valid PDF
            return False, "File is too small to be a valid PDF"
    except Exception as e:
        return False, f"Error checking file size: {str(e)}"
    
    # Check PDF header
    try:
        with open(file_path, 'rb') as f:
            header = f.read(5)
            if header != b'%PDF-':
                return False, "File does not have a valid PDF header"
    except Exception as e:
        return False, f"Error reading file header: {str(e)}"
    
    # Basic validation passed
    return True, None

def check_pdf_issues(file_path: Path) -> Dict[str, Any]:
    """
    Check a PDF file for common issues that might cause processing errors.
    
    Args:
        file_path: Path to the PDF file to check
        
    Returns:
        Dictionary containing:
            - has_issues: Boolean indicating if any issues were found
            - issues: List of issue descriptions
            - warnings: List of warning descriptions
            - info: Additional information about the PDF
    """
    result = {
        "has_issues": False,
        "issues": [],
        "warnings": [],
        "info": {}
    }
    
    # First validate that it's a PDF
    is_valid, error_message = validate_pdf(file_path)
    if not is_valid:
        result["has_issues"] = True
        result["issues"].append(f"Invalid PDF: {error_message}")
        return result
    
    # Check file size
    try:
        file_size = file_path.stat().st_size
        result["info"]["file_size"] = file_size
        
        # Warn about very large files
        if file_size > 100 * 1024 * 1024:  # 100 MB
            result["warnings"].append(f"PDF file is very large ({file_size / (1024 * 1024):.2f} MB), which may cause processing issues")
    except Exception as e:
        result["warnings"].append(f"Could not check file size: {str(e)}")
    
    # Try to open with PyPDF2 to check for encryption and other issues
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            try:
                pdf_reader = PyPDF2.PdfReader(f)
                
                # Check if encrypted
                if pdf_reader.is_encrypted:
                    result["has_issues"] = True
                    result["issues"].append("PDF is encrypted/password-protected and cannot be processed")
                
                # Get page count
                page_count = len(pdf_reader.pages)
                result["info"]["page_count"] = page_count
                
                # Warn about very large page counts
                if page_count > 1000:
                    result["warnings"].append(f"PDF has a large number of pages ({page_count}), which may cause processing issues")
                
                # Check for metadata
                if pdf_reader.metadata:
                    result["info"]["has_metadata"] = True
                else:
                    result["info"]["has_metadata"] = False
                    result["warnings"].append("PDF does not have metadata, which may indicate a non-standard PDF")
                
            except Exception as e:
                result["has_issues"] = True
                result["issues"].append(f"Error reading PDF with PyPDF2: {str(e)}")
    except ImportError:
        result["warnings"].append("PyPDF2 is not available, skipping detailed PDF checks")
    
    # Try to open with pdfplumber to check for content extraction issues
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            try:
                # Try to extract text from the first page
                if pdf.pages:
                    first_page = pdf.pages[0]
                    text = first_page.extract_text()
                    
                    if not text:
                        result["warnings"].append("First page does not contain extractable text, PDF may be scanned or contain only images")
                    
                    # Check for images
                    if hasattr(first_page, 'images') and first_page.images:
                        result["info"]["has_images"] = True
                    else:
                        result["info"]["has_images"] = False
                    
                    # Check for tables
                    tables = first_page.find_tables()
                    if tables:
                        result["info"]["has_tables"] = True
                    else:
                        result["info"]["has_tables"] = False
                
            except Exception as e:
                result["warnings"].append(f"Error extracting content with pdfplumber: {str(e)}")
    except ImportError:
        result["warnings"].append("pdfplumber is not available, skipping content extraction checks")
    
    return result
