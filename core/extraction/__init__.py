"""
Extraction module for the Searchable PDF Library.

This module provides functionality for extracting structured data from PDF documents, including:
- Extracting tables
- Extracting form fields
- Converting extracted data to various formats (CSV, Excel, JSON)
"""

from .extractor import DataExtractor

__all__ = ['DataExtractor']
