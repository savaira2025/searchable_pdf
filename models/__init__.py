"""
Data models for the Searchable PDF Library.

This module provides data models for representing PDF documents, search queries, and other entities.
"""

from .document import (
    DocumentMetadata,
    PageInfo,
    TableInfo,
    SearchQuery,
    SearchResultItem,
    SearchResult,
    Entity,
    DocumentSummary
)

__all__ = [
    'DocumentMetadata',
    'PageInfo',
    'TableInfo',
    'SearchQuery',
    'SearchResultItem',
    'SearchResult',
    'Entity',
    'DocumentSummary'
]
