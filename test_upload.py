#!/usr/bin/env python3
"""
Test script to upload a PDF file and check if the response contains properly serialized datetime objects.
"""

import requests
import json
import sys
from pathlib import Path

def main():
    """Main entry point for the test script."""
    # Check if the API server is running
    try:
        response = requests.get("http://localhost:8000/api")
        if response.status_code != 200:
            print(f"Error: API server returned status code {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server. Make sure it's running.")
        return
    
    # Upload a PDF file
    pdf_file = Path("tests/test_data/sample.pdf")
    if not pdf_file.exists():
        print(f"Error: PDF file not found: {pdf_file}")
        return
    
    # Send a POST request to upload the PDF file
    files = {"file": (pdf_file.name, open(pdf_file, "rb"), "application/pdf")}
    data = {"collection": "test"}
    
    try:
        response = requests.post("http://localhost:8000/documents/upload", files=files, data=data)
        if response.status_code != 200:
            print(f"Error: Upload failed with status code {response.status_code}")
            print(response.text)
            
            # Try to get more detailed error information
            try:
                error_data = response.json()
                if 'detail' in error_data:
                    print(f"Error detail: {error_data['detail']}")
            except Exception as e:
                print(f"Could not parse error response: {str(e)}")
            
            return
        
        # Parse the response
        result = response.json()
        
        # Check if the response contains datetime fields
        datetime_fields = ["upload_date", "creation_date", "modification_date"]
        for field in datetime_fields:
            if field in result:
                print(f"{field}: {result[field]}")
                # Check if the field is a string (properly serialized)
                if not isinstance(result[field], str) and result[field] is not None:
                    print(f"Error: {field} is not properly serialized. Type: {type(result[field])}")
                    return
        
        print("Success! All datetime fields are properly serialized.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return

if __name__ == "__main__":
    main()
