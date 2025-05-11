#!/usr/bin/env python3
"""
Basic tests for the Searchable PDF Library.
This script tests the core functionality of the library.
"""

import os
import sys
import unittest
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document.processor import PDFProcessor
from core.search.engine import SearchEngine
from core.extraction.extractor import DataExtractor
from core.analytics.analyzer import ContentAnalyzer

class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality of the Searchable PDF Library."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Create test directories
        cls.test_dir = Path("tests/test_data")
        cls.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test storage directories
        cls.storage_dir = cls.test_dir / "storage"
        cls.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components with test storage
        cls.pdf_processor = PDFProcessor(str(cls.storage_dir))
        cls.search_engine = SearchEngine(str(cls.storage_dir))
        cls.data_extractor = DataExtractor(str(cls.storage_dir))
        cls.content_analyzer = ContentAnalyzer(str(cls.storage_dir))
        
        # Test PDF file path
        cls.test_pdf = cls.test_dir / "sample.pdf"
        
        # Check if test PDF exists
        if not cls.test_pdf.exists():
            print(f"Warning: Test PDF file not found at {cls.test_pdf}")
            print("Some tests may fail. Please create a sample PDF file for testing.")
    
    def test_pdf_processor_initialization(self):
        """Test that the PDF processor initializes correctly."""
        self.assertIsNotNone(self.pdf_processor)
        self.assertEqual(str(self.pdf_processor.base_dir), str(self.storage_dir))
        self.assertTrue(self.pdf_processor.uploads_dir.exists())
        self.assertTrue(self.pdf_processor.processed_dir.exists())
        self.assertTrue(self.pdf_processor.metadata_file.exists())
    
    def test_search_engine_initialization(self):
        """Test that the search engine initializes correctly."""
        self.assertIsNotNone(self.search_engine)
        self.assertEqual(str(self.search_engine.base_dir), str(self.storage_dir))
        self.assertTrue(self.search_engine.index_dir.exists())
    
    def test_data_extractor_initialization(self):
        """Test that the data extractor initializes correctly."""
        self.assertIsNotNone(self.data_extractor)
        self.assertEqual(str(self.data_extractor.base_dir), str(self.storage_dir))
        self.assertTrue(self.data_extractor.extracted_dir.exists())
    
    def test_content_analyzer_initialization(self):
        """Test that the content analyzer initializes correctly."""
        self.assertIsNotNone(self.content_analyzer)
        self.assertEqual(str(self.content_analyzer.base_dir), str(self.storage_dir))
        self.assertTrue(self.content_analyzer.analytics_dir.exists())
    
    @unittest.skipIf(not Path("tests/test_data/sample.pdf").exists(), "Test PDF file not found")
    def test_pdf_processing(self):
        """Test processing a PDF document."""
        # Process the test PDF
        metadata = self.pdf_processor.process(self.test_pdf, "test")
        
        # Check that metadata was created
        self.assertIsNotNone(metadata)
        self.assertIsNotNone(metadata.id)
        self.assertEqual(metadata.filename, self.test_pdf.name)
        self.assertEqual(metadata.collection, "test")
        self.assertTrue(metadata.processed)
        
        # Check that the document was copied to the processed directory
        processed_file = self.pdf_processor.processed_dir / metadata.id / self.test_pdf.name
        self.assertTrue(processed_file.exists())
        
        # Check that text was extracted
        self.assertIsNotNone(metadata.text_path)
        text_file = Path(metadata.text_path)
        self.assertTrue(text_file.exists())
        
        # Return the document ID for use in other tests
        return metadata.id
    
    @unittest.skipIf(not Path("tests/test_data/sample.pdf").exists(), "Test PDF file not found")
    def test_full_workflow(self):
        """Test the full workflow: process, index, search, extract, analyze."""
        # Process the PDF
        doc_id = self.test_pdf_processing()
        
        # Index the document
        indexed = self.search_engine.index_document(doc_id)
        self.assertTrue(indexed)
        
        # Search for content
        # This is a simple search that should match most documents
        results = self.search_engine.search("the")
        self.assertGreater(results.total_results, 0)
        
        # Extract text
        text = self.data_extractor.extract_text(doc_id)
        self.assertIsNotNone(text)
        self.assertGreater(len(text), 0)
        
        # Generate summary
        summary = self.content_analyzer.generate_summary(doc_id)
        self.assertIsNotNone(summary)
        self.assertGreater(len(summary), 0)
        
        # Extract entities
        entities = self.content_analyzer.extract_entities(doc_id)
        self.assertIsNotNone(entities)
        
        # Delete the document
        deleted = self.pdf_processor.delete_document(doc_id)
        self.assertTrue(deleted)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures."""
        # Remove test storage directory
        import shutil
        if cls.storage_dir.exists():
            shutil.rmtree(cls.storage_dir)

if __name__ == "__main__":
    unittest.main()
