#!/usr/bin/env python3
"""
PDF Table Extractor - Robust macOS Version with Enhanced Error Handling

This version includes comprehensive error handling for common PDF table extraction issues.
"""

import pandas as pd
import pdfplumber
import tabula
import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')
pd.options.mode.chained_assignment = None

@dataclass
class TableInfo:
    """Information about an extracted table."""
    page_number: int
    table_number: int
    data: pd.DataFrame
    confidence: float
    method: str

class PDFTableExtractorRobust:
    """
    Robust PDF table extractor for macOS with comprehensive error handling.
    """
    
    def __init__(self, pdf_path: str, debug: bool = False):
        self.pdf_path = Path(pdf_path)
        self.setup_logging(debug)
        self.validate_pdf()
    
    def setup_logging(self, debug: bool):
        """Setup logging configuration."""
        level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_pdf(self):
        """Validate the PDF file."""
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        
        if not self.pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"File must be a PDF: {self.pdf_path}")
    
    def safe_dataframe_creation(self, table_data: List[List], page_num: int, table_num: int) -> Optional[pd.DataFrame]:
        """Safely create DataFrame from table data with robust error handling."""
        try:
            if not table_data or len(table_data) == 0:
                return None
            
            # Remove completely empty rows
            filtered_data = [row for row in table_data if any(cell and str(cell).strip() for cell in row)]
            
            if not filtered_data:
                return None
            
            # Create DataFrame
            df = pd.DataFrame(filtered_data)
            
            if df.empty:
                return None
            
            # Handle columns safely
            num_cols = len(df.columns)
            
            # Create safe column names
            temp_columns = [f'col_{i}' for i in range(num_cols)]
            df.columns = temp_columns
            
            # Try to use first row as header if it looks like headers
            if len(df) > 1:
                first_row = df.iloc[0]
                # Check if first row contains non-numeric data (likely headers)
                is_header = True
                for val in first_row:
                    if val is not None and str(val).strip():
                        try:
                            float(str(val).replace('$', '').replace(',', ''))
                            # If we can convert to float, might be data not header
                            pass
                        except (ValueError, TypeError):
                            # Non-numeric, likely header
                            continue
                
                # Use first row as header if it's not all numeric
                try:
                    header_values = [str(val).strip() if val is not None else f'Column_{i}' for i, val in enumerate(first_row)]
                    
                    # Ensure unique column names
                    unique_headers = []
                    for header in header_values:
                        base_header = header if header else f'Column_{len(unique_headers)}'
                        counter = 1
                        final_header = base_header
                        while final_header in unique_headers:
                            final_header = f"{base_header}_{counter}"
                            counter += 1
                        unique_headers.append(final_header)
                    
                    df.columns = unique_headers
                    df = df.iloc[1:].reset_index(drop=True)
                    
                except Exception as e:
                    self.logger.warning(f"Could not set headers for table {table_num} on page {page_num}: {e}")
                    # Keep default column names
                    pass
            
            # Final cleanup
            df = self.clean_dataframe_robust(df)
            
            return df if not df.empty else None
            
        except Exception as e:
            self.logger.error(f"Error creating DataFrame for table {table_num} on page {page_num}: {e}")
            return None
    
    def clean_dataframe_robust(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame with robust error handling."""
        try:
            if df.empty:
                return df
            
            # Drop completely empty rows and columns
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            if df.empty:
                return df
            
            # Clean string values safely
            for col in df.columns:
                try:
                    df[col] = df[col].apply(lambda x: str(x).strip() if x is not None and str(x).strip() else None)
                except Exception:
                    continue
            
            # Replace empty strings with None
            df = df.replace('', None)
            df = df.replace('nan', None)
            
            return df
            
        except Exception as e:
            self.logger.warning(f"Error cleaning DataFrame: {e}")
            return df
    
    def extract_with_pdfplumber(self) -> List[TableInfo]:
        """Extract tables using pdfplumber with robust error handling."""
        self.logger.info("Extracting tables with pdfplumber...")
        tables = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_tables = page.find_tables()
                        self.logger.debug(f"Page {page_num}: Found {len(page_tables)} potential tables")
                        
                        for table_num, table in enumerate(page_tables, 1):
                            try:
                                table_data = table.extract()
                                
                                if table_data:
                                    df = self.safe_dataframe_creation(table_data, page_num, table_num)
                                    
                                    if df is not None and not df.empty:
                                        table_info = TableInfo(
                                            page_number=page_num,
                                            table_number=table_num,
                                            data=df,
                                            confidence=0.9,
                                            method='pdfplumber'
                                        )
                                        tables.append(table_info)
                                        self.logger.debug(f"Successfully extracted table {table_num} on page {page_num}: {df.shape}")
                                
                            except Exception as e:
                                self.logger.warning(f"Error extracting table {table_num} on page {page_num}: {e}")
                                continue
                                
                    except Exception as e:
                        self.logger.warning(f"Error processing page {page_num}: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Error opening PDF with pdfplumber: {e}")
        
        return tables
    
    def extract_with_tabula(self) -> List[TableInfo]:
        """Extract tables using tabula-py with robust error handling."""
        self.logger.info("Extracting tables with tabula-py...")
        tables = []
        
        try:
            dfs = tabula.read_pdf(
                str(self.pdf_path),
                pages='all',
                multiple_tables=True,
                pandas_options={'header': None},
                silent=True
            )
            
            for i, df in enumerate(dfs):
                if not df.empty and df.shape[0] > 0:
                    try:
                        # Convert table data to list format for consistent processing
                        table_data = df.values.tolist()
                        processed_df = self.safe_dataframe_creation(table_data, i + 1, i + 1)
                        
                        if processed_df is not None and not processed_df.empty:
                            table_info = TableInfo(
                                page_number=i + 1,  # Approximate
                                table_number=i + 1,
                                data=processed_df,
                                confidence=0.8,
                                method='tabula'
                            )
                            tables.append(table_info)
                            self.logger.debug(f"Tabula found table {i+1}: {processed_df.shape}")
                    
                    except Exception as e:
                        self.logger.warning(f"Error processing tabula table {i+1}: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Error with tabula extraction: {e}")
        
        return tables
    
    def combine_table_group_robust(self, table_group: List[TableInfo]) -> pd.DataFrame:
        """Combine tables with robust error handling."""
        if len(table_group) == 1:
            return self.clean_dataframe_robust(table_group[0].data)
        
        try:
            combined_data = []
            reference_columns = None
            
            for table_info in table_group:
                df = table_info.data.copy()
                df = self.clean_dataframe_robust(df)
                
                if df.empty:
                    continue
                
                if reference_columns is None:
                    reference_columns = list(df.columns)
                    combined_data.append(df)
                else:
                    # Try to align columns
                    if len(df.columns) == len(reference_columns):
                        df.columns = reference_columns
                    combined_data.append(df)
            
            if not combined_data:
                return pd.DataFrame()
            
            # Combine with error handling
            result = pd.concat(combined_data, ignore_index=True, sort=False)
            return self.clean_dataframe_robust(result)
            
        except Exception as e:
            self.logger.error(f"Error combining table group: {e}")
            # Return the first table as fallback
            return self.clean_dataframe_robust(table_group[0].data) if table_group else pd.DataFrame()
    
    def extract_all_tables(self) -> List[pd.DataFrame]:
        """Extract all tables with comprehensive error handling."""
        self.logger.info(f"Starting table extraction from {self.pdf_path}")
        
        all_tables = []
        
        # Try pdfplumber first (most reliable on macOS)
        try:
            pdfplumber_tables = self.extract_with_pdfplumber()
            if pdfplumber_tables:
                self.logger.info(f"pdfplumber found {len(pdfplumber_tables)} tables")
                all_tables.extend(pdfplumber_tables)
        except Exception as e:
            self.logger.error(f"pdfplumber failed: {e}")
        
        # Try tabula as backup/additional source
        try:
            tabula_tables = self.extract_with_tabula()
            if tabula_tables:
                self.logger.info(f"tabula found {len(tabula_tables)} additional tables")
                all_tables.extend(tabula_tables)
        except Exception as e:
            self.logger.error(f"tabula failed: {e}")
        
        if not all_tables:
            self.logger.warning("No tables found with any extraction method")
            return []
        
        # Group and combine tables
        try:
            table_groups = self.detect_table_continuity(all_tables)
            combined_tables = []
            
            for group_num, group in enumerate(table_groups, 1):
                try:
                    combined_df = self.combine_table_group_robust(group)
                    if not combined_df.empty:
                        combined_tables.append(combined_df)
                        self.logger.info(f"Combined table group {group_num}: {combined_df.shape}")
                except Exception as e:
                    self.logger.error(f"Error combining group {group_num}: {e}")
                    # Add individual tables as fallback
                    for table_info in group:
                        clean_df = self.clean_dataframe_robust(table_info.data)
                        if not clean_df.empty:
                            combined_tables.append(clean_df)
            
            return combined_tables
            
        except Exception as e:
            self.logger.error(f"Error in table grouping: {e}")
            # Return individual tables as fallback
            return [self.clean_dataframe_robust(table_info.data) for table_info in all_tables 
                   if not self.clean_dataframe_robust(table_info.data).empty]
    
    def detect_table_continuity(self, tables: List[TableInfo]) -> List[List[TableInfo]]:
        """Detect table continuity with error handling."""
        if not tables:
            return []
        
        try:
            sorted_tables = sorted(tables, key=lambda t: (t.page_number, t.table_number))
            groups = []
            current_group = [sorted_tables[0]]
            
            for current_table in sorted_tables[1:]:
                try:
                    last_table = current_group[-1]
                    
                    # Check if tables are similar (same column count)
                    if (len(current_table.data.columns) == len(last_table.data.columns) and
                        current_table.page_number <= last_table.page_number + 1):
                        current_group.append(current_table)
                    else:
                        groups.append(current_group)
                        current_group = [current_table]
                
                except Exception as e:
                    self.logger.warning(f"Error in continuity detection: {e}")
                    groups.append(current_group)
                    current_group = [current_table]
            
            groups.append(current_group)
            return groups
            
        except Exception as e:
            self.logger.error(f"Error in table continuity detection: {e}")
            # Return each table as its own group
            return [[table] for table in tables]
    
    def process_pdf(self, merge_similar: bool = True) -> List[pd.DataFrame]:
        """Process PDF and return combined tables (Streamlit compatibility method)."""
        return self.extract_all_tables()
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """Get summary of extraction process (Streamlit compatibility method)."""
        try:
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
                    'methods_used': ['pdfplumber', 'tabula-py (robust)']
                }
        except Exception as e:
            self.logger.warning(f"Could not generate summary: {e}")
            return {
                'total_pages': 0,
                'pages_with_tables': 0,
                'total_tables': 0,
                'methods_used': ['pdfplumber', 'tabula-py (robust)']
            }

    def export_to_csv(self, tables: List[pd.DataFrame], output_path: str = "extracted_tables.csv"):
        """Export tables to CSV with error handling."""
        try:
            if len(tables) == 1:
                tables[0].to_csv(output_path, index=False)
                self.logger.info(f"Exported single table to {output_path}")
            else:
                # Combine all tables
                combined = pd.concat(tables, ignore_index=True, sort=False)
                combined.to_csv(output_path, index=False)
                self.logger.info(f"Exported {len(tables)} combined tables to {output_path}")
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def export_to_excel(self, tables: List[pd.DataFrame], output_path: str = "extracted_tables.xlsx"):
        """Export tables to Excel with error handling."""
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for i, table in enumerate(tables, 1):
                    sheet_name = f'Table_{i}'
                    table.to_excel(writer, sheet_name=sheet_name, index=False)
            
            self.logger.info(f"Exported {len(tables)} tables to {output_path}")
        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {e}")
            raise
    
    def export_to_html(self, tables: List[pd.DataFrame], output_path: str = "extracted_tables.html"):
        """Export tables to HTML with error handling."""
        try:
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Extracted PDF Tables</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; font-weight: bold; }
                    .table-title { color: #333; margin-top: 30px; }
                </style>
            </head>
            <body>
                <h1>Extracted PDF Tables</h1>
            """
            
            for i, table in enumerate(tables, 1):
                html_content += f'<h2 class="table-title">Table {i}</h2>\n'
                html_content += table.to_html(index=False, escape=False, classes='data-table')
                html_content += '\n'
            
            html_content += """
            </body>
            </html>
            """
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Exported {len(tables)} tables to {output_path}")
        except Exception as e:
            self.logger.error(f"Error exporting to HTML: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Extract tables from PDF files (macOS Robust Version)')
    parser.add_argument('pdf_file', help='Path to the PDF file')
    parser.add_argument('--format', choices=['csv', 'excel', 'html', 'all'], 
                       default='csv', help='Output format')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    try:
        # Create extractor
        extractor = PDFTableExtractorRobust(args.pdf_file, debug=args.debug)
        
        # Extract tables
        tables = extractor.extract_all_tables()
        
        if not tables:
            print("❌ No tables found in the PDF")
            return
        
        # Export in requested format(s)
        if args.format in ['csv', 'all']:
            extractor.export_to_csv(tables)
        
        if args.format in ['excel', 'all']:
            extractor.export_to_excel(tables)
        
        if args.format in ['html', 'all']:
            extractor.export_to_html(tables)
        
        print(f"✅ Successfully extracted {len(tables)} tables")
        for i, table in enumerate(tables, 1):
            print(f"   Table {i}: {table.shape[0]} rows × {table.shape[1]} columns")
    
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        logging.error(f"Full error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
