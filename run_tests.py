#!/usr/bin/env python3
"""
Run tests for the Searchable PDF Library.
This script provides a simple way to run the tests.
"""

import os
import sys
import unittest
from pathlib import Path

def main():
    """Run the tests."""
    # Change to the script's directory
    os.chdir(Path(__file__).parent)
    
    # Check if test data is available
    test_data_dir = Path("tests/test_data")
    sample_pdf = test_data_dir / "sample.pdf"
    
    if not sample_pdf.exists():
        print("Warning: Test PDF file not found at", sample_pdf)
        print("Some tests may be skipped. See tests/test_data/README.md for more information.")
    
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover("tests")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return non-zero exit code if tests failed
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
