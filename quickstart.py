#!/usr/bin/env python3
"""
Quickstart script for the Searchable PDF Library.
This script demonstrates how to quickly get started with the library.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the quickstart script."""
    print("=== Searchable PDF Library Quickstart ===")
    print()
    
    # Change to the script's directory
    os.chdir(Path(__file__).parent)
    
    # Check if sample PDF exists
    sample_pdf = Path("tests/test_data/sample.pdf")
    if not sample_pdf.exists():
        print("Generating sample PDF...")
        try:
            subprocess.run([sys.executable, "examples/generate_sample_pdf.py"], check=True)
            print()
        except subprocess.CalledProcessError:
            print("Error generating sample PDF. Make sure reportlab is installed:")
            print("pip install reportlab")
            return
    
    # Run the example script
    print("Running basic usage example...")
    try:
        subprocess.run([sys.executable, "examples/basic_usage.py"], check=True)
        print()
    except subprocess.CalledProcessError:
        print("Error running example script.")
        return
    
    # Start the web interface
    print("Starting web interface...")
    print("Press Ctrl+C to stop the server.")
    try:
        subprocess.run([sys.executable, "run.py", "web"], check=True)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except subprocess.CalledProcessError:
        print("Error starting web interface.")
        return

if __name__ == "__main__":
    main()
