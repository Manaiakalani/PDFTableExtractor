"""
Advanced Table Processing Utilities

Additional utilities for handling complex table extraction scenarios,
data cleaning, and format conversion.
"""

import pandas as pd
import numpy as np
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging


class TableProcessor:
    """Advanced table processing utilities."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def detect_numeric_columns(self, df: pd.DataFrame) -> List[str]:
        """Detect columns that should be numeric but are stored as strings."""
        numeric_cols = []
        
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                # If more than 70% of values can be converted to numeric
                if numeric_series.count() / len(df) > 0.7:
                    numeric_cols.append(col)
        
        return numeric_cols
    
    def clean_currency_columns(self, df: pd.DataFrame, 
                             currency_cols: Optional[List[str]] = None) -> pd.DataFrame:
        """Clean currency columns by removing symbols and converting to float."""
        df_clean = df.copy()
        
        if currency_cols is None:
            # Auto-detect currency columns
            currency_cols = []
            for col in df.columns:
                if df[col].dtype == 'object':
                    sample_values = df[col].dropna().astype(str).head(10)
                    if sample_values.str.contains(r'[$€£¥₹]').any():
                        currency_cols.append(col)
        
        for col in currency_cols:
            if col in df_clean.columns:
                # Remove currency symbols and commas
                df_clean[col] = (df_clean[col]
                               .astype(str)
                               .str.replace(r'[$€£¥₹,]', '', regex=True)
                               .str.replace(r'[^\d.-]', '', regex=True))
                
                # Convert to numeric
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                self.logger.info(f"Cleaned currency column: {col}")
        
        return df_clean
    
    def standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names for consistency."""
        df_clean = df.copy()
        
        # Clean column names
        new_columns = []
        for col in df_clean.columns:
            # Convert to string and clean
            clean_col = str(col).strip()
            # Remove special characters and replace with underscore
            clean_col = re.sub(r'[^\w\s]', '_', clean_col)
            # Replace multiple spaces with single underscore
            clean_col = re.sub(r'\s+', '_', clean_col)
            # Convert to lowercase
            clean_col = clean_col.lower()
            # Remove leading/trailing underscores
            clean_col = clean_col.strip('_')
            # Handle empty column names
            if not clean_col or clean_col == 'unnamed':
                clean_col = f'column_{len(new_columns)}'
            
            new_columns.append(clean_col)
        
        df_clean.columns = new_columns
        return df_clean
    
    def detect_table_headers(self, df: pd.DataFrame) -> Tuple[bool, int]:
        """Detect if table has headers and where they are located."""
        if df.empty:
            return False, 0
        
        # Check each row to see if it looks like headers
        for row_idx in range(min(3, len(df))):  # Check first 3 rows
            row = df.iloc[row_idx]
            
            # Count how many values look like headers (text, not numbers)
            text_count = 0
            for val in row:
                if pd.notna(val):
                    str_val = str(val).strip()
                    # Check if it's primarily text (not a number)
                    if (str_val and 
                        not str_val.replace('.', '').replace(',', '').replace('-', '').isdigit() and
                        not re.match(r'^[$€£¥₹]?[\d,.-]+$', str_val)):
                        text_count += 1
            
            # If more than 70% are text-like, consider it headers
            if text_count / len(row) > 0.7:
                return True, row_idx
        
        return False, 0
    
    def merge_split_tables(self, tables: List[pd.DataFrame], 
                          similarity_threshold: float = 0.8) -> List[pd.DataFrame]:
        """Merge tables that were split across pages or methods."""
        if len(tables) <= 1:
            return tables
        
        merged_groups = []
        used_indices = set()
        
        for i, table1 in enumerate(tables):
            if i in used_indices:
                continue
            
            current_group = [table1]
            used_indices.add(i)
            
            for j in range(i + 1, len(tables)):
                if j in used_indices:
                    continue
                
                table2 = tables[j]
                
                # Check column similarity
                cols1 = set(table1.columns)
                cols2 = set(table2.columns)
                
                if len(cols1) > 0 and len(cols2) > 0:
                    similarity = len(cols1.intersection(cols2)) / len(cols1.union(cols2))
                    
                    if similarity >= similarity_threshold:
                        current_group.append(table2)
                        used_indices.add(j)
                        self.logger.info(f"Merged table {j+1} with group (similarity: {similarity:.2f})\")\n            
            merged_groups.append(current_group)\n        
        # Combine each group\n        merged_tables = []\n        for group in merged_groups:\n            if len(group) == 1:\n                merged_tables.append(group[0])\n            else:\n                try:\n                    # Concatenate tables in the group\n                    combined = pd.concat(group, ignore_index=True, sort=False)\n                    merged_tables.append(combined)\n                except Exception as e:\n                    self.logger.warning(f\"Failed to merge group: {e}\")\n                    merged_tables.extend(group)\n        \n        return merged_tables\n    \n    def remove_duplicate_headers(self, df: pd.DataFrame) -> pd.DataFrame:\n        \"\"\"Remove duplicate header rows within the data.\"\"\"\n        if df.empty:\n            return df\n        \n        df_clean = df.copy()\n        header_row = df_clean.columns.tolist()\n        \n        # Find rows that match the header\n        header_mask = df_clean.apply(\n            lambda row: row.astype(str).str.lower().tolist() == \n                       [str(col).lower() for col in header_row], \n            axis=1\n        )\n        \n        # Remove duplicate header rows\n        if header_mask.any():\n            rows_removed = header_mask.sum()\n            df_clean = df_clean[~header_mask]\n            self.logger.info(f\"Removed {rows_removed} duplicate header rows\")\n        \n        return df_clean.reset_index(drop=True)\n    \n    def fix_merged_cells(self, df: pd.DataFrame) -> pd.DataFrame:\n        \"\"\"Fix issues caused by merged cells in the original PDF.\"\"\"\n        df_clean = df.copy()\n        \n        # Forward fill for likely merged cells (empty cells that should repeat previous value)\n        for col in df_clean.columns:\n            # Check if column has pattern of alternating values and NaN\n            non_null_indices = df_clean[col].dropna().index\n            if len(non_null_indices) > 1:\n                # Check if there are regular gaps\n                gaps = np.diff(non_null_indices)\n                if len(set(gaps)) <= 2 and max(gaps) <= 5:  # Regular pattern with small gaps\n                    df_clean[col] = df_clean[col].fillna(method='ffill')\n                    self.logger.info(f\"Forward filled column: {col}\")\n        \n        return df_clean\n    \n    def validate_table_structure(self, df: pd.DataFrame) -> Dict[str, any]:\n        \"\"\"Validate table structure and suggest improvements.\"\"\"\n        validation = {\n            'is_valid': True,\n            'issues': [],\n            'suggestions': [],\n            'metrics': {}\n        }\n        \n        # Basic metrics\n        validation['metrics'] = {\n            'rows': len(df),\n            'columns': len(df.columns),\n            'completeness': (df.count().sum() / (len(df) * len(df.columns))) * 100,\n            'duplicate_rows': df.duplicated().sum(),\n            'empty_columns': (df.count() == 0).sum()\n        }\n        \n        # Check for issues\n        if validation['metrics']['completeness'] < 50:\n            validation['issues'].append(\"Low data completeness (<50%)\")\n            validation['suggestions'].append(\"Review extraction parameters or PDF quality\")\n        \n        if validation['metrics']['duplicate_rows'] > 0:\n            validation['issues'].append(f\"{validation['metrics']['duplicate_rows']} duplicate rows found\")\n            validation['suggestions'].append(\"Remove duplicate rows\")\n        \n        if validation['metrics']['empty_columns'] > 0:\n            validation['issues'].append(f\"{validation['metrics']['empty_columns']} empty columns found\")\n            validation['suggestions'].append(\"Remove empty columns\")\n        \n        # Check column name quality\n        unnamed_cols = [col for col in df.columns if 'unnamed' in str(col).lower()]\n        if unnamed_cols:\n            validation['issues'].append(f\"Found {len(unnamed_cols)} unnamed columns\")\n            validation['suggestions'].append(\"Review header detection and column naming\")\n        \n        validation['is_valid'] = len(validation['issues']) == 0\n        \n        return validation


class PDFTableAnalyzer:
    \"\"\"Analyze PDF table extraction results and provide insights.\"\"\"\n    
    def __init__(self, tables: List[pd.DataFrame]):\n        self.tables = tables        self.processor = TableProcessor()\n    \n    def generate_extraction_report(self) -> Dict[str, any]:\n        \"\"\"Generate a comprehensive extraction report.\"\"\"\n        report = {\n            'summary': {\n                'total_tables': len(self.tables),\n                'total_rows': sum(len(table) for table in self.tables),\n                'total_columns': sum(len(table.columns) for table in self.tables),\n                'avg_completeness': 0\n            },\n            'table_details': [],\n            'quality_issues': [],\n            'recommendations': []\n        }\n        \n        completeness_scores = []\n        \n        for i, table in enumerate(self.tables, 1):\n            validation = self.processor.validate_table_structure(table)\n            completeness_scores.append(validation['metrics']['completeness'])\n            \n            table_detail = {\n                'table_number': i,\n                'shape': table.shape,\n                'completeness': validation['metrics']['completeness'],\n                'issues': validation['issues'],\n                'column_types': {str(dtype): count for dtype, count in table.dtypes.value_counts().items()}\n            }\n            \n            report['table_details'].append(table_detail)\n            report['quality_issues'].extend(validation['issues'])\n            report['recommendations'].extend(validation['suggestions'])\n        \n        if completeness_scores:\n            report['summary']['avg_completeness'] = np.mean(completeness_scores)\n        \n        # Global recommendations\n        if report['summary']['avg_completeness'] < 70:\n            report['recommendations'].append(\"Consider preprocessing PDF or using different extraction method\")\n        \n        if len(set(report['quality_issues'])) > 3:\n            report['recommendations'].append(\"Multiple quality issues detected - manual review recommended\")\n        \n        return report\n    \n    def create_data_dictionary(self) -> pd.DataFrame:\n        \"\"\"Create a data dictionary for all extracted tables.\"\"\"\n        dictionary_data = []\n        \n        for table_num, table in enumerate(self.tables, 1):\n            for col in table.columns:\n                col_data = {\n                    'table_number': table_num,\n                    'column_name': col,\n                    'data_type': str(table[col].dtype),\n                    'non_null_count': table[col].count(),\n                    'null_count': table[col].isnull().sum(),\n                    'unique_values': table[col].nunique(),\n                    'completeness_pct': (table[col].count() / len(table)) * 100\n                }\n                \n                # Add sample values\n                sample_values = table[col].dropna().unique()[:3]\n                col_data['sample_values'] = ', '.join(str(val) for val in sample_values)\n                \n                dictionary_data.append(col_data)\n        \n        return pd.DataFrame(dictionary_data)\n    \n    def suggest_data_types(self, table: pd.DataFrame) -> Dict[str, str]:\n        \"\"\"Suggest appropriate data types for each column.\"\"\"\n        suggestions = {}\n        \n        for col in table.columns:\n            current_type = str(table[col].dtype)\n            \n            if current_type == 'object':\n                # Check if it should be numeric\n                numeric_convertible = pd.to_numeric(table[col], errors='coerce').count()\n                if numeric_convertible / len(table) > 0.8:\n                    # Check if it's integer or float\n                    numeric_values = pd.to_numeric(table[col], errors='coerce').dropna()\n                    if (numeric_values % 1 == 0).all():\n                        suggestions[col] = 'int64'\n                    else:\n                        suggestions[col] = 'float64'\n                \n                # Check if it should be datetime\n                elif table[col].astype(str).str.match(r'\\d{4}-\\d{2}-\\d{2}|\\d{2}/\\d{2}/\\d{4}').any():\n                    suggestions[col] = 'datetime64[ns]'\n                \n                # Check if it should be category\n                elif table[col].nunique() / len(table) < 0.1:  # Less than 10% unique values\n                    suggestions[col] = 'category'\n        \n        return suggestions


def batch_process_pdfs(pdf_directory: str, output_directory: str = None) -> Dict[str, List[pd.DataFrame]]:
    \"\"\"Process multiple PDF files in a directory.\"\"\"\n    from pdf_table_extractor import PDFTableExtractor\n    \n    pdf_dir = Path(pdf_directory)\n    if output_directory:\n        output_dir = Path(output_directory)\n        output_dir.mkdir(exist_ok=True)\n    else:\n        output_dir = pdf_dir / \"extracted_tables\"\n        output_dir.mkdir(exist_ok=True)\n    \n    results = {}\n    \n    # Find all PDF files\n    pdf_files = list(pdf_dir.glob(\"*.pdf\"))\n    \n    if not pdf_files:\n        raise FileNotFoundError(f\"No PDF files found in {pdf_directory}\")\n    \n    print(f\"Found {len(pdf_files)} PDF files to process\")\n    \n    for pdf_path in pdf_files:\n        print(f\"\\nProcessing: {pdf_path.name}\")\n        \n        try:\n            # Extract tables\n            extractor = PDFTableExtractor(str(pdf_path))\n            tables = extractor.process_pdf(\n                merge_similar=True,\n                output_format='all',\n                output_path=str(output_dir / pdf_path.stem)\n            )\n            \n            results[pdf_path.name] = tables\n            print(f\"  ✅ Extracted {len(tables)} tables\")\n            \n        except Exception as e:\n            print(f\"  ❌ Error processing {pdf_path.name}: {e}\")\n            results[pdf_path.name] = []\n    \n    return results


def create_master_workbook(tables_dict: Dict[str, List[pd.DataFrame]], 
                          output_path: str = \"master_extracted_tables.xlsx\"):\n    \"\"\"Create a master Excel workbook with all extracted tables.\"\"\"\n    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:\n        sheet_num = 1\n        \n        # Create summary sheet\n        summary_data = []\n        for pdf_name, tables in tables_dict.items():\n            for i, table in enumerate(tables, 1):\n                summary_data.append({\n                    'PDF_File': pdf_name,\n                    'Table_Number': i,\n                    'Rows': len(table),\n                    'Columns': len(table.columns),\n                    'Sheet_Name': f'T{sheet_num}_{pdf_name[:10]}_{i}'\n                })\n                sheet_num += 1\n        \n        if summary_data:\n            summary_df = pd.DataFrame(summary_data)\n            summary_df.to_excel(writer, sheet_name='Summary', index=False)\n        \n        # Add individual tables\n        sheet_num = 1\n        for pdf_name, tables in tables_dict.items():\n            for i, table in enumerate(tables, 1):\n                sheet_name = f'T{sheet_num}_{pdf_name[:10]}_{i}'[:31]  # Excel sheet name limit\n                table.to_excel(writer, sheet_name=sheet_name, index=False)\n                sheet_num += 1\n    \n    print(f\"✅ Created master workbook: {output_path}\")\n    return output_path


# Example usage functions
def example_advanced_cleaning():
    \"\"\"Example of advanced table cleaning.\"\"\"\n    # Sample messy data\n    messy_data = {\n        'Product Name ': ['  Widget A  ', 'Widget B', '  Widget C'],\n        'Price($)': ['$10.50', '$15.00', '$8.75'],\n        '  Quantity  ': ['100', '50', '75'],\n        'Date': ['2024-01-01', '2024-01-02', '2024-01-03']\n    }\n    \n    df = pd.DataFrame(messy_data)\n    processor = TableProcessor()\n    \n    print(\"Original data:\")\n    print(df)\n    print(f\"Data types: {df.dtypes.to_dict()}\")\n    \n    # Clean column names\n    df_clean = processor.standardize_column_names(df)\n    print(\"\\nAfter standardizing column names:\")\n    print(df_clean)\n    \n    # Clean currency columns\n    df_clean = processor.clean_currency_columns(df_clean)\n    print(\"\\nAfter cleaning currency:\")\n    print(df_clean)\n    print(f\"Data types: {df_clean.dtypes.to_dict()}\")\n    \n    return df_clean


if __name__ == \"__main__\":\n    # Run example\n    example_advanced_cleaning()
