"""
Analytics module for the Searchable PDF Library.

This module provides functionality for analyzing PDF document content, including:
- Generating summaries
- Extracting named entities
- Performing sentiment analysis
- Topic modeling
"""

from .analyzer import ContentAnalyzer

__all__ = ['ContentAnalyzer']
