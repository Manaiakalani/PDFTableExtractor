#!/usr/bin/env python3
"""
PDF Table Extractor - macOS Compatible Version

A streamlined version that works well on macOS without requiring complex dependencies.
Uses pdfplumber and tabula-py for reliable table extraction.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass

import pandas as pd
import tabula
import pdfplumber
from bs4 import BeautifulSoup


@dataclass
class TableInfo:
    """Information about an extracted table."""
    page_number: int
    table_number: int
    data: pd.DataFrame
    confidence: float
    method: str


class PDFTableExtractorMacOS:
    """macOS-optimized PDF table extractor."""
    
    def __init__(self, pdf_path: str, debug: bool = False):
        """Initialize the PDF table extractor."""
        self.pdf_path = Path(pdf_path)
        self.tables: List[TableInfo] = []
        self.setup_logging(debug)
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    def setup_logging(self, debug: bool):
        """Setup logging configuration."""
        level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('pdf_extraction.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def extract_with_tabula(self) -> List[TableInfo]:
        """Extract tables using tabula-py."""
        self.logger.info("Extracting tables with tabula-py...")
        tables = []
        
        try:
            dfs = tabula.read_pdf(
                str(self.pdf_path),
                pages='all',
                multiple_tables=True,
                pandas_options={'header': None}
            )
            
            for i, df in enumerate(dfs):
                if not df.empty and df.shape[0] > 0:
                    # Reset column names to avoid duplicates
                    df.columns = [f'col_{j}' for j in range(len(df.columns))]
                    
                    # Use first row as header if appropriate
                    if len(df) > 1:
                        first_row = df.iloc[0].astype(str)
                        if not first_row.str.match(r'^\d+\.?\d*$').all():
                            df.columns = first_row.tolist()
                            df = df.iloc[1:].reset_index(drop=True)
                    
                    table_info = TableInfo(
                        page_number=i + 1,
                        table_number=i + 1,
                        data=df,
                        confidence=0.8,
                        method='tabula'
                    )
                    tables.append(table_info)
                    self.logger.debug(f"Found table {i+1} with shape {df.shape}")
        
        except Exception as e:
            self.logger.error(f"Error with tabula extraction: {e}")
        
        return tables
    
    def extract_with_pdfplumber(self) -> List[TableInfo]:
        """Extract tables using pdfplumber."""
        self.logger.info("Extracting tables with pdfplumber...")
        tables = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        # Find all tables on this page
                        page_tables = page.find_tables()
                        
                        for table_num, table in enumerate(page_tables, 1):
                            try:
                                # Extract table data
                                table_data = table.extract()
                                
                                if table_data and len(table_data) > 0:
                                    # Convert to DataFrame with safe column handling
                                    df = pd.DataFrame(table_data)
                                    
                                    # Handle empty DataFrame
                                    if df.empty:
                                        continue
                                    
                                    # Reset column names to avoid duplicates
                                    df.columns = [f'col_{i}' for i in range(len(df.columns))]
                                    
                                    # Use first row as header if it looks like one
                                    if len(df) > 1:
                                        first_row = df.iloc[0].astype(str)
                                        if not first_row.str.match(r'^\d+\.?\d*$').all():
                                            # First row doesn't look like numeric data, use as header
                                            df.columns = first_row.tolist()
                                            df = df.iloc[1:].reset_index(drop=True)
                                    
                                    table_info = TableInfo(
                                        page_number=page_num,
                                        table_number=table_num,
                                        data=df,
                                        confidence=0.9,
                                        method='pdfplumber'
                                    )
                                    tables.append(table_info)
                                    self.logger.debug(f"Found table {table_num} on page {page_num}")
                                    
                            except Exception as e:
                                self.logger.warning(f"Error extracting table {table_num} on page {page_num}: {e}")
                                continue
                                
                    except Exception as e:
                        self.logger.warning(f"Error processing page {page_num}: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Error with pdfplumber extraction: {e}")
        
        return tables
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize a DataFrame."""
        if df.empty:
            return df
            
        # Drop completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Clean string values
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        # Replace empty strings with NaN
        df = df.replace('', pd.NA)
        
        # Handle duplicate column names
        if df.columns.duplicated().any():
            new_columns = []
            for i, col in enumerate(df.columns):
                if df.columns.tolist().count(col) > 1:
                    count = df.columns[:i+1].tolist().count(col)
                    new_columns.append(f"{col}_{count}" if count > 1 else col)
                else:
                    new_columns.append(col)
            df.columns = new_columns
        
        return df
    
    def process_pdf(self, merge_similar: bool = True) -> List[pd.DataFrame]:
        """Process PDF and return combined tables (Streamlit compatibility method)."""
        return self.extract_all_tables()
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """Get summary of extraction process (Streamlit compatibility method)."""
        try:
            # Quick analysis to get summary stats
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                pages_with_tables = 0
                total_tables = 0
                
                for page in pdf.pages:
                    tables = page.find_tables()
                    if tables:
                        pages_with_tables += 1
                        total_tables += len(tables)
                
                return {
                    'total_pages': total_pages,
                    'pages_with_tables': pages_with_tables,
                    'total_tables': total_tables,
                    'methods_used': ['pdfplumber', 'tabula-py']
                }
        except Exception as e:
            self.logger.warning(f"Could not generate summary: {e}")
            return {
                'total_pages': 0,
                'pages_with_tables': 0,
                'total_tables': 0,
                'methods_used': ['pdfplumber', 'tabula-py']
            }

    def detect_table_continuity(self, tables: List[TableInfo]) -> List[List[TableInfo]]:
        """Detect which tables are continuations of each other across pages."""
        if not tables:
            return []
        
        sorted_tables = sorted(tables, key=lambda t: (t.page_number, t.table_number))
        groups = []
        current_group = [sorted_tables[0]]
        
        for i in range(1, len(sorted_tables)):
            current_table = sorted_tables[i]
            previous_table = sorted_tables[i-1]
            
            current_cols = len(current_table.data.columns)
            previous_cols = len(previous_table.data.columns)
            
            is_continuation = (
                current_table.page_number == previous_table.page_number + 1 and
                abs(current_cols - previous_cols) <= 1 and
                current_table.table_number == 1
            )
            
            if is_continuation:
                current_group.append(current_table)
            else:
                groups.append(current_group)
                current_group = [current_table]
        
        groups.append(current_group)
        return groups
    
    def combine_table_group(self, table_group: List[TableInfo]) -> pd.DataFrame:
        """Combine a group of related tables into a single DataFrame."""
        if len(table_group) == 1:
            return self.clean_dataframe(table_group[0].data)
        
        combined_data = []
        header = None
        
        for i, table_info in enumerate(table_group):
            df = table_info.data.copy()
            
            # Clean the dataframe first
            df = self.clean_dataframe(df)
            
            if df.empty:
                continue
                
            if i == 0:
                # Use the first non-empty table as the header reference
                header = df.columns.tolist()
                combined_data.append(df)
            else:
                # Try to align columns with the header
                if len(df.columns) == len(header):
                    df.columns = header
                    # Skip the first row if it looks like a header
                    if not df.empty and df.iloc[0].astype(str).str.lower().tolist() == [str(h).lower() for h in header]:
                        df = df.iloc[1:]
                    if not df.empty:
                        combined_data.append(df)
                else:
                    # If column count doesn't match, add as separate table
                    combined_data.append(df)
        
        if not combined_data:
            return pd.DataFrame()
            
        try:
            result = pd.concat(combined_data, ignore_index=True)
            return self.clean_dataframe(result)
        except Exception as e:
            self.logger.error(f"Error combining tables: {e}")
            # Return the first table if combination fails
            return combined_data[0] if combined_data else pd.DataFrame()
    
    def extract_all_tables(self) -> List[pd.DataFrame]:
        """Extract tables using available methods."""
        self.logger.info(f"Starting table extraction from {self.pdf_path}")
        
        all_tables = []
        
        # Try pdfplumber first (works best on macOS)
        pdfplumber_tables = self.extract_with_pdfplumber()
        if pdfplumber_tables:
            self.logger.info(f"pdfplumber found {len(pdfplumber_tables)} tables")
            all_tables.extend(pdfplumber_tables)
        
        # Try tabula as backup
        if not all_tables:
            tabula_tables = self.extract_with_tabula()
            if tabula_tables:
                self.logger.info(f"tabula found {len(tabula_tables)} tables")
                all_tables.extend(tabula_tables)
        
        self.tables = all_tables
        
        # Group related tables
        table_groups = self.detect_table_continuity(self.tables)
        
        # Combine each group
        combined_tables = []
        for i, group in enumerate(table_groups):
            combined_df = self.combine_table_group(group)
            if not combined_df.empty:
                combined_tables.append(combined_df)
                self.logger.info(f"Combined table group {i+1}: {combined_df.shape}")
        
        return combined_tables
    
    def export_to_csv(self, tables: List[pd.DataFrame], output_path: str):
        """Export tables to CSV format."""
        output_path = Path(output_path)
        
        if len(tables) == 1:
            csv_path = output_path.with_suffix('.csv')
            tables[0].to_csv(csv_path, index=False)
            self.logger.info(f"Exported single table to {csv_path}")
        else:
            for i, table in enumerate(tables, 1):
                csv_path = output_path.with_suffix(f'_table_{i}.csv')
                table.to_csv(csv_path, index=False)
                self.logger.info(f"Exported table {i} to {csv_path}")
    
    def export_to_excel(self, tables: List[pd.DataFrame], output_path: str):
        """Export tables to Excel format."""
        excel_path = Path(output_path).with_suffix('.xlsx')
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for i, table in enumerate(tables, 1):
                sheet_name = f'Table_{i}' if len(tables) > 1 else 'Combined_Table'
                table.to_excel(writer, sheet_name=sheet_name, index=False)
        
        self.logger.info(f"Exported {len(tables)} tables to {excel_path}")
    
    def export_to_html(self, tables: List[pd.DataFrame], output_path: str):
        """Export tables to HTML format."""
        html_path = Path(output_path).with_suffix('.html')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Extracted PDF Tables</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>Extracted PDF Tables</h1>
            <p>Source: {self.pdf_path.name}</p>
        """
        
        for i, table in enumerate(tables, 1):
            title = f"Table {i}" if len(tables) > 1 else "Combined Table"
            html_content += f"""
            <h2>{title}</h2>
            {table.to_html(index=False, escape=False)}
            """
        
        html_content += "</body></html>"
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Exported {len(tables)} tables to {html_path}")
    
    def process_pdf(self, merge_similar: bool = True, 
                   output_format: str = 'csv', 
                   output_path: str = None) -> List[pd.DataFrame]:
        """Main method to process the PDF and extract all tables."""
        tables = self.extract_all_tables()
        
        if not tables:
            self.logger.warning("No tables found in the PDF")
            return []
        
        if output_path:
            if output_format in ['csv', 'all']:
                self.export_to_csv(tables, output_path)
            if output_format in ['excel', 'all']:
                self.export_to_excel(tables, output_path)
            if output_format in ['html', 'all']:
                self.export_to_html(tables, output_path)
        
        return tables


def main():
    """Command-line interface for the PDF table extractor."""
    parser = argparse.ArgumentParser(description="Extract tables from PDFs on macOS")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("-o", "--output", default="extracted_tables", help="Output file path")
    parser.add_argument("-f", "--format", choices=['csv', 'excel', 'html', 'all'], 
                       default='csv', help="Output format")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    try:
        extractor = PDFTableExtractorMacOS(args.pdf_path, debug=args.debug)
        tables = extractor.process_pdf(
            output_format=args.format,
            output_path=args.output
        )
        
        print(f"✅ Successfully extracted {len(tables)} tables")
        for i, table in enumerate(tables, 1):
            print(f"   Table {i}: {table.shape[0]} rows × {table.shape[1]} columns")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
