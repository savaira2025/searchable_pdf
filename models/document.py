from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

class DocumentMetadata(BaseModel):
    """
    Metadata for a PDF document in the library.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    title: Optional[str] = None
    author: Optional[str] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    page_count: int
    file_size: int  # in bytes
    collection: Optional[str] = None
    upload_date: datetime = Field(default_factory=datetime.now)
    processed: bool = False
    indexed: bool = False
    has_text: bool = True
    has_tables: bool = False
    has_images: bool = False
    path: str
    text_path: Optional[str] = None
    
    def to_json_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a JSON-serializable dictionary with datetime objects converted to strings.
        
        Returns:
            Dictionary with all datetime objects converted to ISO format strings
        """
        data = self.dict()
        # Convert datetime objects to strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
    class Config:
        schema_extra = {
            "example": {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "filename": "sample.pdf",
                "title": "Sample Document",
                "author": "John Doe",
                "creation_date": "2023-01-15T12:00:00",
                "modification_date": "2023-01-20T15:30:00",
                "page_count": 10,
                "file_size": 1024000,
                "collection": "reports",
                "upload_date": "2023-11-01T10:15:30",
                "processed": True,
                "indexed": True,
                "has_text": True,
                "has_tables": True,
                "has_images": False,
                "path": "storage/uploads/sample.pdf",
                "text_path": "storage/processed/f47ac10b-58cc-4372-a567-0e02b2c3d479/text.txt"
            }
        }

class PageInfo(BaseModel):
    """
    Information about a specific page in a PDF document.
    """
    page_number: int
    width: float
    height: float
    has_text: bool = True
    has_tables: bool = False
    has_images: bool = False
    word_count: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "page_number": 1,
                "width": 612.0,
                "height": 792.0,
                "has_text": True,
                "has_tables": True,
                "has_images": False,
                "word_count": 500
            }
        }

class TableInfo(BaseModel):
    """
    Information about a table extracted from a PDF document.
    """
    document_id: str
    page_number: int
    table_number: int
    rows: int
    columns: int
    bbox: List[float]  # [x0, y0, x1, y1]
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "page_number": 3,
                "table_number": 1,
                "rows": 5,
                "columns": 4,
                "bbox": [100.0, 200.0, 500.0, 400.0]
            }
        }

class FigureInfo(BaseModel):
    """
    Information about a figure extracted from a PDF document.
    """
    document_id: str
    page_number: int
    figure_number: int
    width: int
    height: int
    bbox: List[float]  # [x0, y0, x1, y1]
    format: str  # "jpg", "png", etc.
    filename: str
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "page_number": 2,
                "figure_number": 1,
                "width": 500,
                "height": 300,
                "bbox": [100.0, 200.0, 600.0, 500.0],
                "format": "jpg",
                "filename": "figure_2_1.jpg"
            }
        }

class SearchQuery(BaseModel):
    """
    Query parameters for searching documents.
    """
    text: str
    collection: Optional[str] = None
    metadata_filters: Optional[Dict[str, Any]] = None
    page: int = 1
    limit: int = 10
    
    class Config:
        schema_extra = {
            "example": {
                "text": "climate change",
                "collection": "research",
                "metadata_filters": {
                    "author": "Jane Smith",
                    "creation_date": {"$gt": "2022-01-01"}
                },
                "page": 1,
                "limit": 10
            }
        }

class SearchResultItem(BaseModel):
    """
    A single search result item.
    """
    document_id: str
    document_title: Optional[str] = None
    document_filename: str
    collection: Optional[str] = None
    page_number: Optional[int] = None
    score: float
    highlight: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "document_title": "Climate Change Report 2023",
                "document_filename": "climate_report_2023.pdf",
                "collection": "research",
                "page_number": 5,
                "score": 0.85,
                "highlight": "...significant impact of <em>climate change</em> on coastal regions..."
            }
        }

class SearchResult(BaseModel):
    """
    Search results container.
    """
    query: str
    total_results: int
    page: int
    limit: int
    total_pages: int
    results: List[SearchResultItem]
    
    class Config:
        schema_extra = {
            "example": {
                "query": "climate change",
                "total_results": 42,
                "page": 1,
                "limit": 10,
                "total_pages": 5,
                "results": [
                    {
                        "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                        "document_title": "Climate Change Report 2023",
                        "document_filename": "climate_report_2023.pdf",
                        "collection": "research",
                        "page_number": 5,
                        "score": 0.85,
                        "highlight": "...significant impact of <em>climate change</em> on coastal regions..."
                    }
                ]
            }
        }

class Entity(BaseModel):
    """
    A named entity extracted from document text.
    """
    text: str
    label: str  # PERSON, ORG, GPE, DATE, etc.
    count: int
    pages: List[int]
    
    class Config:
        schema_extra = {
            "example": {
                "text": "United Nations",
                "label": "ORG",
                "count": 15,
                "pages": [1, 3, 5, 8]
            }
        }

class DocumentSummary(BaseModel):
    """
    A summary of a document's content.
    """
    document_id: str
    summary: str
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "summary": "This report examines the impact of climate change on coastal regions..."
            }
        }
