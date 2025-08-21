# PDF Table Extractor - macOS Setup Guide

## Quick Start for macOS

### Prerequisites
- Python 3.9+ (check with `python3 --version`)
- Java 8+ (required for tabula-py)

### Installation

1. **Install Java** (if not already installed):
   ```bash
   brew install openjdk@11
   ```

2. **Install Python dependencies**:
   ```bash
   # Core dependencies (all working on macOS)
   python3 -m pip install pandas==2.3.2 pdfplumber==0.11.7 tabula-py==2.10.0
   python3 -m pip install streamlit==1.48.1 openpyxl==3.1.5 beautifulsoup4==4.12.3
   python3 -m pip install reportlab==4.2.5 matplotlib==3.9.4 seaborn==0.13.2
   ```

### Usage Options

#### 1. Command Line (Recommended for macOS)
```bash
# Extract tables to all formats
python3 pdf_extractor_macos.py your_file.pdf --format all

# Extract to specific format
python3 pdf_extractor_macos.py your_file.pdf --format csv
python3 pdf_extractor_macos.py your_file.pdf --format excel
python3 pdf_extractor_macos.py your_file.pdf --format html

# With debug output
python3 pdf_extractor_macos.py your_file.pdf --format all --debug
```

#### 2. Web Interface
```bash
# Start the web interface
python3 -m streamlit run streamlit_app.py

# Then open http://localhost:8501 in your browser
```

#### 3. Test with Sample Data
```bash
# Generate a test PDF with tables
python3 generate_test_pdf.py

# Extract from the test file
python3 pdf_extractor_macos.py test_sample.pdf --format all
```

### Output Files
- `extracted_tables.csv` - Combined CSV file
- `extracted_tables.xlsx` - Excel file with separate sheets
- `extracted_tables.html` - Formatted HTML file

### Features Working on macOS
- ✅ Multi-page table extraction
- ✅ Table continuity detection across pages
- ✅ CSV, Excel, HTML export
- ✅ Web interface with drag-and-drop
- ✅ Batch processing
- ✅ Data quality assessment

### Known Limitations on macOS
- ⚠️ `camelot-py` requires additional system dependencies (ghostscript)
- ✅ `pdfplumber` and `tabula-py` work perfectly and handle most cases

### For Advanced Features (Optional)
If you want the full-featured version with camelot support:
```bash
# Install system dependencies
brew install ghostscript

# Then install camelot
python3 -m pip install camelot-py[cv]

# Use the full version
python3 pdf_table_extractor.py your_file.pdf --format all
```

### Troubleshooting
- **Java not found**: Install OpenJDK via Homebrew
- **Streamlit command not found**: Use `python3 -m streamlit` instead
- **Permission denied**: Run `chmod +x pdf_extractor_macos.py`
- **Package conflicts**: Use virtual environment

### Next Steps
1. Test with your PDF files using the command line tool
2. Use the web interface for easier operation
3. Customize the extraction parameters in the code as needed

The macOS version provides excellent table extraction capabilities without complex dependencies!
