# PDF Table Extractor

A comprehensive Python tool for extracting tables from multi-page PDFs and combining them into structured outputs. Supports export to CSV, Excel, and HTML formats with preserved formatting and automatic table continuity detection.

## Features

- **Multi-method extraction**: Uses tabula-py, camelot, and pdfplumber for robust table detection
- **Cross-page continuity**: Automatically detects and combines tables that span multiple pages
- **Multiple export formats**: CSV, Excel, and HTML with preserved formatting
- **Smart table merging**: Combines tables with similar column structures
- **Web interface**: User-friendly Streamlit interface for non-technical users
- **Command-line interface**: Scriptable CLI for automation
- **Comprehensive logging**: Detailed extraction process logging

## Installation

1. **Clone or download the project files**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install system dependencies** (for camelot):
   
   **macOS**:
   ```bash
   brew install ghostscript
   ```
   
   **Ubuntu/Debian**:
   ```bash
   sudo apt-get install ghostscript
   ```
   
   **Windows**:
   - Download and install Ghostscript from: https://www.ghostscript.com/download/gsdnld.html

## Quick Start

### Command Line Usage

```bash
# Basic extraction to CSV
python pdf_table_extractor.py document.pdf

# Extract to Excel with custom output name
python pdf_table_extractor.py document.pdf --output my_tables --format excel

# Extract to all formats without merging similar tables
python pdf_table_extractor.py document.pdf --format all --no-merge

# Enable debug mode for troubleshooting
python pdf_table_extractor.py document.pdf --debug
```

### Web Interface

Launch the user-friendly web interface:

```bash
streamlit run streamlit_app.py
```

Then open your browser to the displayed URL (usually `http://localhost:8501`).

### Programmatic Usage

```python
from pdf_table_extractor import PDFTableExtractor

# Create extractor instance
extractor = PDFTableExtractor("document.pdf")

# Extract and process tables
tables = extractor.process_pdf(
    merge_similar=True,
    output_format='excel',
    output_path='extracted_tables'
)

# Work with the extracted DataFrames
for i, table in enumerate(tables, 1):
    print(f"Table {i}: {table.shape}")
    print(table.head())
```

## How It Works

### Extraction Methods

The tool uses three different extraction methods and automatically selects the best results:

1. **pdfplumber**: Excellent for text-based tables and simple layouts
2. **camelot**: Best for tables with clear borders and complex structures
3. **tabula-py**: Good general-purpose extraction with Java-based engine

### Table Continuity Detection

The tool automatically detects tables that continue across pages by analyzing:
- Column structure similarity
- Page sequence patterns
- Table positioning on pages
- Header repetition patterns

### Smart Merging

Tables with similar column structures can be automatically merged:
- Compares column names and count
- Aligns headers across tables
- Removes duplicate headers
- Preserves data integrity

## Output Formats

### CSV Export
- Single table: `output.csv`
- Multiple tables: `output_table_1.csv`, `output_table_2.csv`, etc.

### Excel Export
- Multiple sheets in a single file
- Auto-adjusted column widths
- Preserved formatting

### HTML Export
- Styled HTML with embedded CSS
- Table metadata and statistics
- Responsive design

## Configuration Options

### Command Line Arguments

```
positional arguments:
  pdf_path              Path to the PDF file

optional arguments:
  -h, --help            Show help message
  -o, --output OUTPUT   Output file path (without extension)
  -f, --format {csv,excel,html,all}
                        Output format (default: csv)
  --no-merge            Don't merge similar tables
  --debug               Enable debug logging
```

### Programmatic Configuration

```python
# Advanced configuration
extractor = PDFTableExtractor("document.pdf", debug=True)

# Custom extraction with specific methods
tables_tabula = extractor.extract_with_tabula()
tables_camelot = extractor.extract_with_camelot()
tables_pdfplumber = extractor.extract_with_pdfplumber()

# Custom merging with similarity threshold
merged = extractor.merge_similar_tables(tables, similarity_threshold=0.9)
```

## Troubleshooting

### Common Issues

1. **No tables found**:
   - Ensure the PDF contains actual tables (not just images)
   - Try different extraction methods individually
   - Check if the PDF is text-based (not scanned)

2. **Poor extraction quality**:
   - Use debug mode to see detailed logs
   - Try adjusting the similarity threshold for merging
   - Consider preprocessing the PDF to improve table clarity

3. **Installation issues**:
   - Make sure Java is installed (required for tabula)
   - Install Ghostscript (required for camelot)
   - Use a virtual environment to avoid conflicts

### Debug Mode

Enable debug mode for detailed extraction information:

```bash
python pdf_table_extractor.py document.pdf --debug
```

This will:
- Show detailed extraction logs
- Save logs to `pdf_extraction.log`
- Display confidence scores for each method
- Show table detection details

## Examples

### Example 1: Financial Reports

```bash
# Extract tables from a financial report
python pdf_table_extractor.py financial_report.pdf \
    --output financial_data \
    --format excel
```

### Example 2: Research Papers

```bash
# Extract tables from research papers with detailed logging
python pdf_table_extractor.py research_paper.pdf \
    --output research_tables \
    --format all \
    --debug
```

### Example 3: Multi-page Invoices

```python
from pdf_table_extractor import PDFTableExtractor

# Extract invoice line items across multiple pages
extractor = PDFTableExtractor("multi_page_invoice.pdf")
tables = extractor.process_pdf(merge_similar=True)

# Process the combined invoice data
if tables:
    invoice_data = tables[0]  # Usually one combined table
    total_amount = invoice_data['Amount'].sum()
    print(f"Total invoice amount: ${total_amount}")
```

## File Structure

```
MoreVibes/
├── pdf_table_extractor.py    # Main extraction tool
├── streamlit_app.py          # Web interface
├── example_usage.py          # Usage examples
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Dependencies

- **tabula-py**: PDF table extraction using Java tabula
- **camelot-py**: Advanced table extraction with computer vision
- **pdfplumber**: Text-based PDF analysis
- **pandas**: Data manipulation and analysis
- **openpyxl**: Excel file handling
- **streamlit**: Web interface framework
- **beautifulsoup4**: HTML processing

## Contributing

Feel free to submit issues and pull requests to improve the tool!

## License

This project is open source. Feel free to use and modify as needed.

---

**Note**: This tool works best with text-based PDFs. For scanned PDFs or image-based tables, consider using OCR preprocessing tools first.
