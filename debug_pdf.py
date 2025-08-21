#!/usr/bin/env python3
"""
Quick debug script to identify the reindexing error
"""
import pandas as pd
import pdfplumber
from pathlib import Path
import sys

def debug_pdf(pdf_path):
    """Debug PDF extraction to find the reindexing issue."""
    print(f"Debugging PDF: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"\n--- Page {page_num} ---")
            
            # Find tables on this page
            tables = page.find_tables()
            print(f"Found {len(tables)} tables")
            
            for table_num, table in enumerate(tables, 1):
                try:
                    # Extract table data
                    table_data = table.extract()
                    print(f"Table {table_num}: {len(table_data)} rows")
                    
                    if table_data:
                        # Create DataFrame
                        df = pd.DataFrame(table_data)
                        print(f"DataFrame shape: {df.shape}")
                        print(f"Columns: {list(df.columns)}")
                        
                        # Check for duplicates
                        if df.columns.duplicated().any():
                            print(f"⚠️  Duplicate columns found: {df.columns[df.columns.duplicated()].tolist()}")
                        
                        # Display first few rows
                        print("First 3 rows:")
                        print(df.head(3))
                        
                except Exception as e:
                    print(f"❌ Error processing table {table_num}: {e}")
                    print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug_pdf(sys.argv[1])
    else:
        debug_pdf("test_sample.pdf")
