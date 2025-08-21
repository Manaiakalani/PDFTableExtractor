#!/usr/bin/env python3
"""
Example usage of the PDF Table Extractor

This script demonstrates different ways to use the PDF table extraction tool.
"""

from pdf_table_extractor import PDFTableExtractor
import pandas as pd
from pathlib import Path


def example_basic_extraction():
    """Basic example of extracting tables from a PDF."""
    print("="*60)
    print("BASIC EXTRACTION EXAMPLE")
    print("="*60)
    
    # Replace with your PDF path
    pdf_path = "sample_document.pdf"
    
    if not Path(pdf_path).exists():
        print(f"⚠️  Sample PDF '{pdf_path}' not found.")
        print("Please replace 'pdf_path' with the path to your PDF file.")
        return
    
    try:
        # Create extractor
        extractor = PDFTableExtractor(pdf_path, debug=True)
        
        # Extract tables
        tables = extractor.extract_all_tables()
        
        # Print basic info
        print(f"Found {len(tables)} tables")
        
        for i, table in enumerate(tables, 1):
            print(f"\nTable {i}:")
            print(f"  Page: {table.page_number}")
            print(f"  Shape: {table.data.shape}")
            print(f"  Method: {table.method}")
            print(f"  Confidence: {table.confidence:.2f}")
            print("  Preview:")
            print(table.data.head().to_string())
    
    except Exception as e:
        print(f"Error: {e}")


def example_advanced_extraction():
    """Advanced example with custom processing and multiple export formats."""
    print("\n" + "="*60)
    print("ADVANCED EXTRACTION EXAMPLE")
    print("="*60)
    
    pdf_path = "sample_document.pdf"
    
    if not Path(pdf_path).exists():
        print(f"⚠️  Sample PDF '{pdf_path}' not found.")
        return
    
    try:
        # Create extractor
        extractor = PDFTableExtractor(pdf_path, debug=False)
        
        # Process with custom settings
        tables = extractor.process_pdf(
            merge_similar=True,
            output_format='all',
            output_path='advanced_output'
        )
        
        # Custom post-processing
        processed_tables = []
        for i, table in enumerate(tables, 1):
            # Example: Clean up common issues
            
            # Remove rows where all values are NaN
            clean_table = table.dropna(how='all')
            
            # Example: Set first row as header if it looks like headers
            if not clean_table.empty:
                first_row = clean_table.iloc[0]
                if first_row.astype(str).str.contains(r'^[A-Za-z\s]+$').all():
                    clean_table.columns = first_row
                    clean_table = clean_table.iloc[1:]
            
            processed_tables.append(clean_table)
            
            print(f"\nProcessed Table {i}:")
            print(f"  Original shape: {table.shape}")
            print(f"  Cleaned shape: {clean_table.shape}")
            print("  Columns:", list(clean_table.columns))
        
        # Save processed tables
        for i, table in enumerate(processed_tables, 1):
            table.to_csv(f'processed_table_{i}.csv', index=False)
            print(f"  Saved to: processed_table_{i}.csv")
    
    except Exception as e:
        print(f"Error: {e}")


def example_programmatic_usage():
    """Example of using the extractor programmatically in your own code."""
    print("\n" + "="*60)
    print("PROGRAMMATIC USAGE EXAMPLE")
    print("="*60)
    
    # This is how you would integrate the extractor into your own application
    
    def extract_and_process_tables(pdf_path: str) -> List[pd.DataFrame]:
        """Extract tables and apply custom business logic."""
        extractor = PDFTableExtractor(pdf_path)
        
        # Get raw extracted tables
        raw_tables = extractor.extract_all_tables()
        
        # Apply custom processing
        processed_tables = []
        for table_info in raw_tables:
            df = table_info.data
            
            # Custom validation
            if df.shape[0] < 2:  # Skip tables with less than 2 rows
                continue
            
            # Custom cleaning
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            # Custom formatting
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.strip()
            
            processed_tables.append(df)
        
        return processed_tables
    
    # Example usage
    print("def extract_and_process_tables(pdf_path: str) -> List[pd.DataFrame]:")
    print("    # Your custom table extraction logic here")
    print("    extractor = PDFTableExtractor(pdf_path)")
    print("    tables = extractor.extract_all_tables()")
    print("    # Apply your custom processing...")
    print("    return processed_tables")


if __name__ == "__main__":
    print("PDF Table Extractor - Example Usage")
    print("This script demonstrates various ways to use the PDF table extraction tool.")
    print("\nNote: Replace 'sample_document.pdf' with the path to your actual PDF file.")
    
    # Run examples
    example_basic_extraction()
    example_advanced_extraction()
    example_programmatic_usage()
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run basic extraction: python pdf_table_extractor.py your_file.pdf")
    print("3. Run web interface: streamlit run streamlit_app.py")
    print("4. Integrate into your code using the programmatic examples above")
