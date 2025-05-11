"""
Search module for the Searchable PDF Library.

This module provides functionality for searching across PDF documents, including:
- Indexing document content
- Performing full-text searches
- Ranking and highlighting search results
"""

from .engine import SearchEngine

__all__ = ['SearchEngine']
