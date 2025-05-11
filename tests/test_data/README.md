# Test Data

This directory contains test data for the Searchable PDF Library tests.

## Adding Test PDFs

To run the tests that require PDF files, you need to add some sample PDF files to this directory:

1. Place a sample PDF file named `sample.pdf` in this directory.
2. Optionally, add other PDF files with different characteristics:
   - `table_sample.pdf`: A PDF with tables
   - `form_sample.pdf`: A PDF with form fields
   - `image_sample.pdf`: A PDF with images

The tests will automatically use these files if they are present.

## Test Storage

When running tests, a `storage` directory will be created here to store processed files. This directory is automatically cleaned up after the tests run.
