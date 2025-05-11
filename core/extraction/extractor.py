import os
import json
import csv
import shutil
import zipfile
import io
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import pdfplumber

from models.document import TableInfo, FigureInfo
from core.document.processor import PDFProcessor
from utils.imports import HAS_PANDAS, pandas, HAS_PILLOW, pillow

class DataExtractor:
    """
    Handles extraction of structured data from PDF documents,
    such as tables, forms, and other structured content.
    """
    
    def __init__(self, base_dir: str = "storage"):
        self.base_dir = Path(base_dir)
        self.extracted_dir = self.base_dir / "extracted"
        self.extracted_dir.mkdir(parents=True, exist_ok=True)
        
        self.pdf_processor = PDFProcessor(base_dir)
    
    def extract_text(self, document_id: str, pages: Optional[str] = None) -> str:
        """
        Extract text from a document, optionally from specific pages.
        
        Args:
            document_id: ID of the document
            pages: Optional string specifying pages to extract from (e.g., "1,3,5-7")
            
        Returns:
            Extracted text
        """
        # Get document metadata
        doc_metadata = self.pdf_processor.get_document(document_id)
        if not doc_metadata:
            raise ValueError(f"Document not found: {document_id}")
        
        # If text has already been extracted, return it
        if doc_metadata.text_path:
            # If no specific pages requested, return all text
            if not pages:
                return self.pdf_processor.get_document_text(document_id) or ""
        
        # Parse page specification
        page_numbers = self._parse_page_spec(pages, doc_metadata.page_count) if pages else None
        
        # If no specific pages requested, return all text
        if not page_numbers:
            return self.pdf_processor.get_document_text(document_id) or ""
        
        # Extract text from specific pages
        file_path = Path(doc_metadata.path)
        if not file_path.exists():
            raise ValueError(f"PDF file not found: {file_path}")
        
        extracted_text = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num in page_numbers:
                if 0 <= page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    text = page.extract_text() or ""
                    extracted_text.append(f"--- Page {page_num + 1} ---\n{text}")
        
        return "\n\n".join(extracted_text)
    
    def extract_tables(
        self, 
        document_id: str, 
        pages: Optional[str] = None,
        output_format: str = "json"
    ) -> Union[List[Dict[str, Any]], str, Path]:
        """
        Extract tables from a document, optionally from specific pages.
        
        Args:
            document_id: ID of the document
            pages: Optional string specifying pages to extract from (e.g., "1,3,5-7")
            output_format: Format to return tables in ("json", "csv", "excel")
            
        Returns:
            Extracted tables in the specified format
        """
        # Get document metadata
        doc_metadata = self.pdf_processor.get_document(document_id)
        if not doc_metadata:
            raise ValueError(f"Document not found: {document_id}")
        
        # Parse page specification
        page_numbers = self._parse_page_spec(pages, doc_metadata.page_count) if pages else None
        
        # Extract tables
        file_path = Path(doc_metadata.path)
        if not file_path.exists():
            raise ValueError(f"PDF file not found: {file_path}")
        
        # Create directory for extracted tables
        doc_extract_dir = self.extracted_dir / document_id
        doc_extract_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract tables from the PDF
        tables_data = []
        table_infos = []
        extraction_errors = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                # If no specific pages requested, process all pages
                if not page_numbers:
                    page_numbers = list(range(len(pdf.pages)))
                
                for page_idx in page_numbers:
                    if 0 <= page_idx < len(pdf.pages):
                        page = pdf.pages[page_idx]
                        
                        # Try different table extraction methods
                        try:
                            # Method 1: Standard table extraction
                            tables = page.extract_tables()
                            
                            if not tables:
                                # Method 2: Try with different settings
                                tables = page.find_tables(
                                    table_settings={
                                        "vertical_strategy": "text",
                                        "horizontal_strategy": "text",
                                        "intersection_tolerance": 5
                                    }
                                )
                                if tables:
                                    tables = [table.extract() for table in tables]
                            
                            # Process extracted tables
                            for table_idx, table in enumerate(tables):
                                # Convert table to a list of dictionaries
                                if table and len(table) > 1:  # Ensure there's at least a header row and one data row
                                    headers = [str(cell).strip() if cell else f"Column{i+1}" for i, cell in enumerate(table[0])]
                                    
                                    # Create table info
                                    table_info = TableInfo(
                                        document_id=document_id,
                                        page_number=page_idx + 1,
                                        table_number=table_idx + 1,
                                        rows=len(table),
                                        columns=len(headers),
                                        bbox=[0, 0, 0, 0]  # Placeholder
                                    )
                                    table_infos.append(table_info)
                                    
                                    # Process table rows
                                    table_rows = []
                                    for row_idx, row in enumerate(table[1:], 1):  # Skip header row
                                        row_dict = {}
                                        for col_idx, cell in enumerate(row):
                                            if col_idx < len(headers):
                                                header = headers[col_idx]
                                                row_dict[header] = cell.strip() if cell else ""
                                        
                                        table_rows.append(row_dict)
                                    
                                    # Add table to results
                                    tables_data.append({
                                        "page": page_idx + 1,
                                        "table": table_idx + 1,
                                        "headers": headers,
                                        "rows": table_rows
                                    })
                        
                        except Exception as e:
                            error_msg = f"Error extracting tables from page {page_idx + 1}: {str(e)}"
                            print(error_msg)
                            extraction_errors.append(error_msg)
                            continue
            
            # If no tables were found and there were errors, raise an exception
            if not tables_data and extraction_errors:
                raise ValueError(f"Failed to extract any tables. Errors: {'; '.join(extraction_errors)}")
            
            # If no tables were found but no errors occurred, it might just be that there are no tables
            if not tables_data:
                print(f"No tables found in document {document_id}")
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error during table extraction: {str(e)}")
            print(f"Traceback: {error_trace}")
            raise ValueError(f"Table extraction failed: {str(e)}")
        
        # Save table information
        tables_dict = [table.dict() for table in table_infos]
        # Convert datetime objects to strings
        tables_dict = self.pdf_processor._convert_datetime_to_str(tables_dict)
        with open(doc_extract_dir / "tables_info.json", 'w') as f:
            json.dump(tables_dict, f)
        
        # Return tables in the requested format
        if output_format == "json":
            # Return JSON data directly
            return tables_data if tables_data else []
        
        elif output_format == "csv":
            # Convert to CSV
            csv_file = doc_extract_dir / "tables.csv"
            # Also create a file with the naming convention expected by the API endpoint
            api_csv_file = self.extracted_dir / f"{document_id}_tables.csv"
            
            with open(csv_file, 'w', newline='') as f:
                if tables_data:
                    for table_data in tables_data:
                        writer = csv.DictWriter(f, fieldnames=table_data["headers"])
                        f.write(f"Page {table_data['page']}, Table {table_data['table']}\n")
                        writer.writeheader()
                        writer.writerows(table_data["rows"])
                        f.write("\n\n")
                else:
                    # Create an empty CSV with a note
                    f.write("No tables found in the document.\n")
            
            # Copy the file to the API-expected location
            try:
                shutil.copy2(csv_file, api_csv_file)
            except Exception as e:
                print(f"Warning: Could not copy CSV file to API location: {str(e)}")
                # Try to create the file directly at the API location
                try:
                    with open(api_csv_file, 'w', newline='') as f:
                        f.write("No tables found in the document.\n")
                except Exception as e2:
                    print(f"Error creating CSV file at API location: {str(e2)}")
            
            return api_csv_file
        
        elif output_format == "excel":
            # Convert to Excel
            excel_file = doc_extract_dir / "tables.xlsx"
            # Also create a file with the naming convention expected by the API endpoint
            api_excel_file = self.extracted_dir / f"{document_id}_tables.xlsx"
            
            if not HAS_PANDAS:
                raise ImportError("pandas is required for Excel output. Please install pandas: pip install pandas")
            
            with pandas.ExcelWriter(excel_file) as writer:
                if tables_data:
                    for table_data in tables_data:
                        df = pandas.DataFrame(table_data["rows"])
                        sheet_name = f"P{table_data['page']}_T{table_data['table']}"
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    # Create an empty Excel file with a note
                    df = pandas.DataFrame({"Note": ["No tables found in the document."]})
                    df.to_excel(writer, sheet_name="Info", index=False)
            
            # Copy the file to the API-expected location
            try:
                shutil.copy2(excel_file, api_excel_file)
            except Exception as e:
                print(f"Warning: Could not copy Excel file to API location: {str(e)}")
                # Try to create the file directly at the API location
                try:
                    with pandas.ExcelWriter(api_excel_file) as writer:
                        df = pandas.DataFrame({"Note": ["No tables found in the document."]})
                        df.to_excel(writer, sheet_name="Info", index=False)
                except Exception as e2:
                    print(f"Error creating Excel file at API location: {str(e2)}")
            
            return api_excel_file
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def extract_form_fields(self, document_id: str) -> Dict[str, Any]:
        """
        Extract form fields from a PDF document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Dictionary of form field names and values
        """
        # Get document metadata
        doc_metadata = self.pdf_processor.get_document(document_id)
        if not doc_metadata:
            raise ValueError(f"Document not found: {document_id}")
        
        # Extract form fields
        file_path = Path(doc_metadata.path)
        if not file_path.exists():
            raise ValueError(f"PDF file not found: {file_path}")
        
        # This is a simplified implementation
        # pdfplumber doesn't directly support form field extraction
        # For a real implementation, you might use PyPDF2 or another library
        
        form_fields = {}
        
        # Create directory for extracted form data
        doc_extract_dir = self.extracted_dir / document_id
        doc_extract_dir.mkdir(parents=True, exist_ok=True)
        
        # Save form field data
        with open(doc_extract_dir / "form_fields.json", 'w') as f:
            json.dump(form_fields, f)
        
        return form_fields
    
    def extract_figures(
        self, 
        document_id: str, 
        pages: Optional[str] = None,
        output_format: str = "json",
        image_format: str = "jpg"
    ) -> Union[List[Dict[str, Any]], str, Path]:
        """
        Extract figures from a document, optionally from specific pages.
        
        Args:
            document_id: ID of the document
            pages: Optional string specifying pages to extract from (e.g., "1,3,5-7")
            output_format: Format to return figures info in ("json", "zip")
            image_format: Format to save extracted images ("jpg", "png")
            
        Returns:
            Extracted figures information in the specified format
        """
        # Get document metadata
        doc_metadata = self.pdf_processor.get_document(document_id)
        if not doc_metadata:
            raise ValueError(f"Document not found: {document_id}")
        
        # Parse page specification
        page_numbers = self._parse_page_spec(pages, doc_metadata.page_count) if pages else None
        
        # Extract figures
        file_path = Path(doc_metadata.path)
        if not file_path.exists():
            raise ValueError(f"PDF file not found: {file_path}")
        
        # Create directory for extracted figures
        doc_extract_dir = self.extracted_dir / document_id
        doc_extract_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a figures directory
        figures_dir = doc_extract_dir / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract figures from the PDF
        figures_data = []
        figure_infos = []
        extraction_errors = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                # If no specific pages requested, process all pages
                if not page_numbers:
                    page_numbers = list(range(len(pdf.pages)))
                
                for page_idx in page_numbers:
                    if 0 <= page_idx < len(pdf.pages):
                        page = pdf.pages[page_idx]
                        
                        try:
                            # Get images from the page
                            images = page.images
                            
                            for img_idx, img in enumerate(images):
                                try:
                                    # Extract image data
                                    img_bbox = [img['x0'], img['top'], img['x1'], img['bottom']]
                                    img_width = int(img['width'])
                                    img_height = int(img['height'])
                                    
                                    # Generate a filename for the image
                                    img_filename = f"figure_{page_idx + 1}_{img_idx + 1}.{image_format}"
                                    img_path = figures_dir / img_filename
                                    
                                    # Save the image
                                    img_data = img['stream'].get_data()
                                    
                                    # Process image with Pillow if available
                                    if HAS_PILLOW:
                                        try:
                                            # Open image from bytes
                                            from PIL import Image
                                            img_obj = Image.open(io.BytesIO(img_data))
                                            
                                            # Convert to RGB if needed
                                            if img_obj.mode != 'RGB' and image_format.lower() == 'jpg':
                                                img_obj = img_obj.convert('RGB')
                                            
                                            # Save in the requested format
                                            img_obj.save(img_path)
                                        except Exception as e:
                                            print(f"Warning: Error processing image with Pillow: {str(e)}")
                                            # Fallback: save raw image data
                                            with open(img_path, 'wb') as f:
                                                f.write(img_data)
                                    else:
                                        # Save raw image data
                                        with open(img_path, 'wb') as f:
                                            f.write(img_data)
                                    
                                    # Create figure info
                                    figure_info = FigureInfo(
                                        document_id=document_id,
                                        page_number=page_idx + 1,
                                        figure_number=img_idx + 1,
                                        width=img_width,
                                        height=img_height,
                                        bbox=img_bbox,
                                        format=image_format,
                                        filename=img_filename
                                    )
                                    figure_infos.append(figure_info)
                                    
                                    # Add figure to results
                                    figures_data.append({
                                        "page": page_idx + 1,
                                        "figure": img_idx + 1,
                                        "width": img_width,
                                        "height": img_height,
                                        "bbox": img_bbox,
                                        "format": image_format,
                                        "filename": img_filename,
                                        "url": f"/files/extracted/{document_id}/figures/{img_filename}"
                                    })
                                except Exception as e:
                                    error_msg = f"Error extracting figure {img_idx + 1} from page {page_idx + 1}: {str(e)}"
                                    print(error_msg)
                                    extraction_errors.append(error_msg)
                                    continue
                        
                        except Exception as e:
                            error_msg = f"Error extracting figures from page {page_idx + 1}: {str(e)}"
                            print(error_msg)
                            extraction_errors.append(error_msg)
                            continue
            
            # If no figures were found and there were errors, raise an exception
            if not figures_data and extraction_errors:
                raise ValueError(f"Failed to extract any figures. Errors: {'; '.join(extraction_errors)}")
            
            # If no figures were found but no errors occurred, it might just be that there are no figures
            if not figures_data:
                print(f"No figures found in document {document_id}")
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error during figure extraction: {str(e)}")
            print(f"Traceback: {error_trace}")
            raise ValueError(f"Figure extraction failed: {str(e)}")
        
        # Save figure information
        figures_dict = [figure.dict() for figure in figure_infos]
        # Convert datetime objects to strings
        figures_dict = self.pdf_processor._convert_datetime_to_str(figures_dict)
        with open(doc_extract_dir / "figures_info.json", 'w') as f:
            json.dump(figures_dict, f)
        
        # Return figures in the requested format
        if output_format == "json":
            # Return JSON data directly
            return figures_data if figures_data else []
        
        elif output_format == "zip":
            # Create a ZIP file containing all figures
            zip_file = doc_extract_dir / "figures.zip"
            api_zip_file = self.extracted_dir / f"{document_id}_figures.zip"
            
            try:
                with zipfile.ZipFile(zip_file, 'w') as zf:
                    # Add each figure to the ZIP
                    for figure_info in figure_infos:
                        img_path = figures_dir / figure_info.filename
                        if img_path.exists():
                            zf.write(img_path, figure_info.filename)
                    
                    # Add metadata JSON
                    metadata_json = json.dumps(figures_dict, indent=2)
                    zf.writestr("figures_info.json", metadata_json)
                
                # Copy the file to the API-expected location
                try:
                    shutil.copy2(zip_file, api_zip_file)
                except Exception as e:
                    print(f"Warning: Could not copy ZIP file to API location: {str(e)}")
                
                return api_zip_file
            
            except Exception as e:
                print(f"Error creating ZIP file: {str(e)}")
                raise ValueError(f"Error creating ZIP file: {str(e)}")
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _parse_page_spec(self, page_spec: str, max_pages: int) -> List[int]:
        """
        Parse a page specification string into a list of page indices.
        
        Args:
            page_spec: String specifying pages (e.g., "1,3,5-7")
            max_pages: Maximum number of pages in the document
            
        Returns:
            List of zero-based page indices
        """
        if not page_spec:
            return list(range(max_pages))
        
        page_indices = []
        
        # Split by comma
        parts = page_spec.split(',')
        
        for part in parts:
            part = part.strip()
            
            # Handle page ranges (e.g., "5-7")
            if '-' in part:
                start, end = part.split('-')
                try:
                    start_idx = int(start.strip()) - 1  # Convert to 0-based index
                    end_idx = int(end.strip()) - 1
                    
                    # Validate range
                    if 0 <= start_idx <= end_idx < max_pages:
                        page_indices.extend(range(start_idx, end_idx + 1))
                except ValueError:
                    # Skip invalid ranges
                    continue
            
            # Handle single pages
            else:
                try:
                    page_idx = int(part) - 1  # Convert to 0-based index
                    
                    # Validate page number
                    if 0 <= page_idx < max_pages:
                        page_indices.append(page_idx)
                except ValueError:
                    # Skip invalid page numbers
                    continue
        
        # Remove duplicates and sort
        return sorted(set(page_indices))
