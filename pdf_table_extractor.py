#!/usr/bin/env python3
"""
PDF Table Extractor

A comprehensive tool for extracting tables from multi-page PDFs and combining them
into structured outputs. Supports export to CSV, Excel, and HTML formats with
preserved formatting and table continuity across pages.

Dependencies:
    pip install tabula-py pandas openpyxl camelot-py[cv] pdfplumber beautifulsoup4

Usage:
    python pdf_table_extractor.py input.pdf --output combined_tables --format csv
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
import camelot
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
    bbox: Optional[Tuple[float, float, float, float]] = None


class PDFTableExtractor:
    """Main class for extracting tables from PDF files."""
    
    def __init__(self, pdf_path: str, debug: bool = False):
        """
        Initialize the PDF table extractor.
        
        Args:
            pdf_path: Path to the PDF file
            debug: Enable debug logging
        """
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
        """Extract tables using tabula-py (good for simple tables)."""
        self.logger.info("Extracting tables with tabula-py...")
        tables = []
        
        try:
            # Read all tables from all pages
            dfs = tabula.read_pdf(
                str(self.pdf_path),
                pages='all',
                multiple_tables=True,
                pandas_options={'header': None}
            )
            
            for i, df in enumerate(dfs):
                if not df.empty and df.shape[0] > 1:  # Skip empty or single-row tables
                    table_info = TableInfo(
                        page_number=i + 1,  # Approximate page number
                        table_number=i + 1,
                        data=df,
                        confidence=0.8,  # Default confidence for tabula
                        method='tabula'
                    )
                    tables.append(table_info)
                    self.logger.debug(f"Found table {i+1} with shape {df.shape}")
        
        except Exception as e:
            self.logger.error(f"Error with tabula extraction: {e}")
        
        return tables
    
    def extract_with_camelot(self) -> List[TableInfo]:
        """Extract tables using camelot (good for complex tables)."""
        self.logger.info("Extracting tables with camelot...")
        tables = []
        
        try:
            # Extract tables from all pages
            camelot_tables = camelot.read_pdf(
                str(self.pdf_path),
                pages='all',
                flavor='lattice'  # Try lattice first for bordered tables
            )
            
            # If lattice doesn't work well, try stream
            if len(camelot_tables) == 0:
                camelot_tables = camelot.read_pdf(
                    str(self.pdf_path),
                    pages='all',
                    flavor='stream'
                )
            
            for i, table in enumerate(camelot_tables):
                if not table.df.empty and table.df.shape[0] > 1:
                    table_info = TableInfo(
                        page_number=table.page,
                        table_number=i + 1,
                        data=table.df,
                        confidence=table.accuracy,
                        method='camelot',
                        bbox=(table.bbox) if hasattr(table, 'bbox') else None
                    )
                    tables.append(table_info)
                    self.logger.debug(f"Found table on page {table.page} with accuracy {table.accuracy:.2f}")
        
        except Exception as e:
            self.logger.error(f"Error with camelot extraction: {e}")
        
        return tables
    
    def extract_with_pdfplumber(self) -> List[TableInfo]:
        """Extract tables using pdfplumber (good for text-based tables)."""
        self.logger.info("Extracting tables with pdfplumber...")
        tables = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    
                    for table_num, table_data in enumerate(page_tables, 1):
                        if table_data and len(table_data) > 1:  # Skip empty or single-row tables
                            # Convert to DataFrame
                            df = pd.DataFrame(table_data[1:], columns=table_data[0])
                            
                            table_info = TableInfo(
                                page_number=page_num,
                                table_number=table_num,
                                data=df,
                                confidence=0.9,  # pdfplumber is generally reliable
                                method='pdfplumber'
                            )
                            tables.append(table_info)
                            self.logger.debug(f"Found table {table_num} on page {page_num}")
        
        except Exception as e:
            self.logger.error(f"Error with pdfplumber extraction: {e}")
        
        return tables
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize a DataFrame."""
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Clean whitespace
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        
        # Replace empty strings with NaN
        df = df.replace('', pd.NA)
        
        return df
    
    def detect_table_continuity(self, tables: List[TableInfo]) -> List[List[TableInfo]]:
        """
        Detect which tables are continuations of each other across pages.
        
        Returns:
            List of table groups, where each group contains tables that should be combined
        """
        if not tables:
            return []
        
        # Sort tables by page number and position
        sorted_tables = sorted(tables, key=lambda t: (t.page_number, t.table_number))
        
        groups = []
        current_group = [sorted_tables[0]]
        
        for i in range(1, len(sorted_tables)):
            current_table = sorted_tables[i]
            previous_table = sorted_tables[i-1]
            
            # Check if tables have similar column structure
            current_cols = len(current_table.data.columns)
            previous_cols = len(previous_table.data.columns)
            
            # Check if it's the next page and similar column count
            is_continuation = (
                current_table.page_number == previous_table.page_number + 1 and
                abs(current_cols - previous_cols) <= 1 and  # Allow slight column difference
                current_table.table_number == 1 and  # Usually first table on next page
                previous_table.table_number == len([t for t in sorted_tables 
                                                   if t.page_number == previous_table.page_number])
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
            
            # Use first table's header as the master header
            if i == 0:
                header = df.columns.tolist()
                combined_data.append(df)
            else:
                # Align columns with master header
                if len(df.columns) == len(header):
                    df.columns = header
                    # Skip header row if it looks like a repeat
                    if not df.iloc[0].equals(pd.Series(header, index=header)):
                        combined_data.append(df)
                    else:
                        combined_data.append(df.iloc[1:])
                else:
                    # Handle column mismatch
                    self.logger.warning(f"Column mismatch in table group. Expected {len(header)}, got {len(df.columns)}")
                    combined_data.append(df)
        
        # Combine all DataFrames
        result = pd.concat(combined_data, ignore_index=True)
        return self.clean_dataframe(result)
    
    def extract_all_tables(self) -> List[pd.DataFrame]:
        """Extract tables using multiple methods and combine results."""
        self.logger.info(f"Starting table extraction from {self.pdf_path}")
        
        all_tables = []
        
        # Try different extraction methods
        methods = [
            ('pdfplumber', self.extract_with_pdfplumber),
            ('camelot', self.extract_with_camelot),
            ('tabula', self.extract_with_tabula)
        ]
        
        best_tables = []
        best_count = 0
        
        for method_name, method_func in methods:
            try:
                tables = method_func()
                self.logger.info(f"{method_name} found {len(tables)} tables")
                
                if len(tables) > best_count:
                    best_tables = tables
                    best_count = len(tables)
                
                all_tables.extend(tables)
            except Exception as e:
                self.logger.error(f"Error with {method_name}: {e}")
        
        # Use the method that found the most tables
        if best_tables:
            self.tables = best_tables
        else:
            self.tables = all_tables
        
        # Group related tables
        table_groups = self.detect_table_continuity(self.tables)
        
        # Combine each group into a single DataFrame
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
            # Single table - save directly
            csv_path = output_path.with_suffix('.csv')
            tables[0].to_csv(csv_path, index=False)
            self.logger.info(f"Exported single table to {csv_path}")
        else:
            # Multiple tables - save each with numbered suffix
            for i, table in enumerate(tables, 1):
                csv_path = output_path.with_suffix(f'_table_{i}.csv')
                table.to_csv(csv_path, index=False)
                self.logger.info(f"Exported table {i} to {csv_path}")
    
    def export_to_excel(self, tables: List[pd.DataFrame], output_path: str):
        """Export tables to Excel format with multiple sheets."""
        excel_path = Path(output_path).with_suffix('.xlsx')
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for i, table in enumerate(tables, 1):
                sheet_name = f'Table_{i}' if len(tables) > 1 else 'Combined_Table'
                table.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        self.logger.info(f"Exported {len(tables)} tables to {excel_path}")
    
    def export_to_html(self, tables: List[pd.DataFrame], output_path: str):
        """Export tables to HTML format."""
        html_path = Path(output_path).with_suffix('.html')
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Extracted PDF Tables</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; font-weight: bold; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .table-header { color: #333; margin-top: 30px; margin-bottom: 10px; }
                .metadata { color: #666; font-size: 0.9em; margin-bottom: 10px; }
            </style>
        </head>
        <body>
            <h1>Extracted PDF Tables</h1>
            <p>Source: {pdf_name}</p>
        """.format(pdf_name=self.pdf_path.name)
        
        for i, table in enumerate(tables, 1):
            title = f"Table {i}" if len(tables) > 1 else "Combined Table"
            html_content += f"""
            <h2 class="table-header">{title}</h2>
            <div class="metadata">Rows: {len(table)}, Columns: {len(table.columns)}</div>
            {table.to_html(index=False, escape=False, classes='table')}
            """
        
        html_content += """
        </body>
        </html>
        """
        
        # Pretty print the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        self.logger.info(f"Exported {len(tables)} tables to {html_path}")
    
    def merge_similar_tables(self, tables: List[pd.DataFrame], 
                           similarity_threshold: float = 0.8) -> List[pd.DataFrame]:
        """
        Merge tables that have similar column structures.
        
        Args:
            tables: List of DataFrames to potentially merge
            similarity_threshold: Minimum similarity score to merge tables
        
        Returns:
            List of merged DataFrames
        """
        if len(tables) <= 1:
            return tables
        
        merged_groups = []
        used_indices = set()
        
        for i, table1 in enumerate(tables):
            if i in used_indices:
                continue
            
            current_group = [table1]
            used_indices.add(i)
            
            for j, table2 in enumerate(tables[i+1:], i+1):
                if j in used_indices:
                    continue
                
                # Check column similarity
                cols1 = set(table1.columns)
                cols2 = set(table2.columns)
                similarity = len(cols1.intersection(cols2)) / len(cols1.union(cols2))
                
                if similarity >= similarity_threshold:
                    current_group.append(table2)
                    used_indices.add(j)
            
            # Merge tables in current group
            if len(current_group) == 1:
                merged_groups.append(current_group[0])
            else:
                # Combine tables with similar structures
                try:
                    merged = pd.concat(current_group, ignore_index=True, sort=False)
                    merged_groups.append(merged)
                    self.logger.info(f"Merged {len(current_group)} similar tables")
                except Exception as e:
                    self.logger.warning(f"Failed to merge tables: {e}")
                    merged_groups.extend(current_group)
        
        return merged_groups
    
    def process_pdf(self, merge_similar: bool = True, 
                   output_format: str = 'csv', 
                   output_path: str = None) -> List[pd.DataFrame]:
        """
        Main method to process the PDF and extract all tables.
        
        Args:
            merge_similar: Whether to merge tables with similar column structures
            output_format: Export format ('csv', 'excel', 'html', or 'all')
            output_path: Output file path (without extension)
        
        Returns:
            List of extracted and processed DataFrames
        """
        # Extract tables
        tables = self.extract_all_tables()
        
        if not tables:
            self.logger.warning("No tables found in the PDF")
            return []
        
        # Convert to DataFrames
        dataframes = [table.data for table in tables]
        
        # Merge similar tables if requested
        if merge_similar:
            dataframes = self.merge_similar_tables(dataframes)
        
        # Export if output path is provided
        if output_path:
            if output_format in ['csv', 'all']:
                self.export_to_csv(dataframes, output_path)
            if output_format in ['excel', 'all']:
                self.export_to_excel(dataframes, output_path)
            if output_format in ['html', 'all']:
                self.export_to_html(dataframes, output_path)
        
        return dataframes
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """Get a summary of the extraction process."""
        if not self.tables:
            return {"status": "No tables extracted"}
        
        summary = {
            "total_tables": len(self.tables),
            "pages_with_tables": len(set(t.page_number for t in self.tables)),
            "extraction_methods": list(set(t.method for t in self.tables)),
            "table_details": []
        }
        
        for table in self.tables:
            summary["table_details"].append({
                "page": table.page_number,
                "table_number": table.table_number,
                "shape": table.data.shape,
                "method": table.method,
                "confidence": table.confidence
            })
        
        return summary


def main():
    """Command-line interface for the PDF table extractor."""
    parser = argparse.ArgumentParser(
        description="Extract tables from multi-page PDFs and export to various formats"
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("-o", "--output", default="extracted_tables", 
                       help="Output file path (without extension)")
    parser.add_argument("-f", "--format", choices=['csv', 'excel', 'html', 'all'], 
                       default='csv', help="Output format")
    parser.add_argument("--no-merge", action="store_true", 
                       help="Don't merge similar tables")
    parser.add_argument("--debug", action="store_true", 
                       help="Enable debug logging")
    
    args = parser.parse_args()
    
    try:
        # Create extractor instance
        extractor = PDFTableExtractor(args.pdf_path, debug=args.debug)
        
        # Process the PDF
        tables = extractor.process_pdf(
            merge_similar=not args.no_merge,
            output_format=args.format,
            output_path=args.output
        )
        
        # Print summary
        summary = extractor.get_extraction_summary()
        print("\n" + "="*50)
        print("EXTRACTION SUMMARY")
        print("="*50)
        print(f"PDF File: {args.pdf_path}")
        print(f"Total tables found: {summary.get('total_tables', 0)}")
        print(f"Pages with tables: {summary.get('pages_with_tables', 0)}")
        print(f"Methods used: {', '.join(summary.get('extraction_methods', []))}")
        print(f"Final combined tables: {len(tables)}")
        
        if tables:
            print("\nTable Details:")
            for i, table in enumerate(tables, 1):
                print(f"  Table {i}: {table.shape[0]} rows × {table.shape[1]} columns")
        
        print(f"\nOutput files saved with prefix: {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
