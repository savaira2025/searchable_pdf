"""
Searchable PDF Library
======================

A library for processing, searching, and extracting data from PDF documents.

This package provides tools for:
- Extracting text and metadata from PDF documents
- Searching across multiple PDF documents
- Extracting tables and other structured data from PDFs
- Analyzing PDF content with NLP techniques

Example usage:
-------------
```python
from searchable_pdf_library.core.document.processor import PDFProcessor
from searchable_pdf_library.core.search.engine import SearchEngine

# Initialize components
pdf_processor = PDFProcessor()
search_engine = SearchEngine()

# Process a PDF document
metadata = pdf_processor.process("path/to/document.pdf", collection="research")

# Index the document for searching
search_engine.index_document(metadata.id)

# Search for content
results = search_engine.search("climate change")
```

For more examples, see the examples directory.
"""

__version__ = "1.0.0"
