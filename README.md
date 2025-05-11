# Searchable PDF

A powerful Python library and API for processing, searching, and extracting data from PDF documents.

## Features

- **PDF Processing**: Extract text, metadata, and structure from PDF documents
- **Full-Text Search**: Search across all your PDF documents with advanced query capabilities
- **Table Extraction**: Automatically detect and extract tables from PDFs to CSV, Excel, or JSON
- **Content Analysis**: Generate summaries and extract named entities from document content
- **Document Translation**: Translate documents to different languages using LLM models
- **API & CLI**: Access functionality through a RESTful API or command-line interface

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/searchable_pdf.git
   cd searchable_pdf
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install spaCy language model (optional, for better entity extraction):
   ```
   python -m spacy download en_core_web_sm
   ```

4. Set up OpenAI API key for translation (optional):
   ```
   # For Linux/macOS
   export OPENAI_API_KEY=your_api_key_here
   
   # For Windows
   set OPENAI_API_KEY=your_api_key_here
   ```
   
   Alternatively, create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
   
   **Note**: For translation functionality to work, you need a valid OpenAI API key that starts with 'sk-'. 
   You can get one from [OpenAI's API Keys page](https://platform.openai.com/api-keys).

## Usage

### API Server

Start the API server:

```
cd searchable_pdf
python main.py
```

The API will be available at http://localhost:8000. You can access the API documentation at http://localhost:8000/docs.

### Command-Line Interface

The library includes a command-line interface for common operations:

```
python cli.py [command] [options]
```

Available commands:

- `upload`: Upload a PDF document to the library
- `list`: List documents in the library
- `get`: Get document metadata
- `delete`: Delete a document
- `search`: Search for documents
- `extract-text`: Extract text from a document
- `extract-tables`: Extract tables from a document
- `summarize`: Generate a summary of a document
- `entities`: Extract entities from a document
- `translate`: Translate a document to a different language
- `index`: Index documents for searching

Examples:

```
# Upload a PDF document
python cli.py upload path/to/document.pdf --collection research

# Search for documents
python cli.py search "climate change" --collection research

# Extract tables from a document
python cli.py extract-tables document_id --format excel --output tables.xlsx

# Generate a summary of a document
python cli.py summarize document_id --max-length 1000 --output summary.txt

# Translate a document to Spanish
python cli.py translate document_id --target-language es --output translated.txt
```

## API Endpoints

The API provides the following endpoints:

- `POST /documents/upload`: Upload a PDF document
- `GET /documents`: List documents in the library
- `GET /documents/{document_id}`: Get document metadata
- `DELETE /documents/{document_id}`: Delete a document
- `POST /search`: Search for documents
- `GET /documents/{document_id}/extract/text`: Extract text from a document
- `GET /documents/{document_id}/extract/tables`: Extract tables from a document
- `GET /documents/{document_id}/analyze/summary`: Generate a summary of a document
- `GET /documents/{document_id}/analyze/entities`: Extract entities from a document
- `GET /documents/{document_id}/translate`: Translate a document to a different language
- `GET /documents/{document_id}/translate/pages`: Translate specific pages of a document
- `POST /translate/text`: Translate arbitrary text

## Project Structure

```
searchable_pdf/
├── api/                  # API endpoints
├── core/                 # Core application logic
│   ├── document/         # Document processing
│   ├── search/           # Search functionality
│   ├── extraction/       # Data extraction
│   ├── analytics/        # Content analysis
│   └── translation/      # Document translation
├── models/               # Data models
├── storage/              # Storage for documents and processed data
├── utils/                # Utility functions
├── config/               # Configuration
├── main.py               # API entry point
└── cli.py                # Command-line interface
```

## Use Cases

### Research Document Management

Organize and search through research papers, extract tables of data, and generate summaries to quickly understand content.

### Legal Document Analysis

Search across case documents for specific legal terms, extract entities (people, organizations, dates), and identify relevant sections.

### Financial Document Processing

Extract data from invoices and financial reports, convert tables to structured formats, and organize documents by collection.

### Academic Paper Analysis

Extract data tables from research papers, find connections between papers, and generate summaries of technical content.

### Multilingual Document Processing

Translate documents to different languages, making content accessible to non-native speakers and enabling cross-language research.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Translation Functionality

The Searchable PDF Library includes powerful translation capabilities that allow you to:

1. **Translate entire documents** to different languages
2. **Translate specific pages** of a document
3. **Translate arbitrary text** through the API

### Translation Requirements

- A valid OpenAI API key is required for translation functionality
- The API key must be a standard OpenAI key that starts with 'sk-'
- Project-level API keys (starting with 'sk-proj-') are not supported by the OpenAI API

### Translation Methods

- **API-based translation**: Uses OpenAI's GPT models for high-quality translation
- **Language detection**: Automatically detects the source language if not specified
- **Caching**: Translations are cached to avoid redundant API calls

### Translation Examples

Using the CLI:
```
# Translate a document to Spanish
python cli.py translate document_id --target-language es --output translated.txt

# Translate specific pages of a document to French
python cli.py translate document_id --target-language fr --pages "1,3,5-7" --output translated.txt
```

Using the API:
```
# Translate a document
GET /documents/{document_id}/translate?target_language=es

# Translate specific pages
GET /documents/{document_id}/translate/pages?target_language=fr&pages=1,3,5-7

# Translate arbitrary text
POST /translate/text
{
  "text": "Hello, world!",
  "target_language": "es"
}
```

## Acknowledgements

- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF parsing and data extraction
- [PyPDF2](https://github.com/py-pdf/pypdf) - PDF processing
- [Whoosh](https://github.com/mchaput/whoosh) - Full-text search
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [spaCy](https://spacy.io/) - Natural language processing
- [langdetect](https://github.com/Mimino666/langdetect) - Language detection
- [OpenAI API](https://platform.openai.com/) - Translation services
