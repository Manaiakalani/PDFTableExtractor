"""
Interactive PDF Table Extractor

A user-friendly interface for extracting tables from PDFs with preview capabilities.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
import zipfile
import io
from pdf_extractor_macos import PDFTableExtractorMacOS as PDFTableExtractor


def main():
    st.set_page_config(
        page_title="PDF Table Extractor",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 PDF Table Extractor")
    st.markdown("Extract and combine tables from multi-page PDFs with ease!")
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    merge_similar = st.sidebar.checkbox(
        "Merge similar tables", 
        value=True,
        help="Automatically combine tables with similar column structures"
    )
    
    export_format = st.sidebar.selectbox(
        "Export Format",
        options=["CSV", "Excel", "HTML", "All"],
        help="Choose the output format for extracted tables"
    )
    
    debug_mode = st.sidebar.checkbox(
        "Debug mode",
        value=False,
        help="Enable detailed logging"
    )
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload a PDF file containing tables to extract"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            # Extract tables
            with st.spinner("Extracting tables from PDF..."):
                extractor = PDFTableExtractor(tmp_path, debug=debug_mode)
                tables = extractor.process_pdf(merge_similar=merge_similar)
            
            if not tables:
                st.error("No tables found in the uploaded PDF.")
                return
            
            # Display extraction summary
            summary = extractor.get_extraction_summary()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tables Found", summary.get('total_tables', 0))
            with col2:
                st.metric("Pages with Tables", summary.get('pages_with_tables', 0))
            with col3:
                st.metric("Final Combined Tables", len(tables))
            
            # Display tables
            st.header("Extracted Tables")
            
            # Table selection
            if len(tables) > 1:
                selected_table = st.selectbox(
                    "Select table to preview:",
                    range(len(tables)),
                    format_func=lambda x: f"Table {x+1} ({tables[x].shape[0]} rows × {tables[x].shape[1]} cols)"
                )
            else:
                selected_table = 0
            
            # Display selected table
            if tables:
                st.subheader(f"Table {selected_table + 1}")
                
                # Table statistics
                table = tables[selected_table]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Rows:** {table.shape[0]}")
                with col2:
                    st.write(f"**Columns:** {table.shape[1]}")
                with col3:
                    st.write(f"**Non-null values:** {table.count().sum()}")
                
                # Display table
                st.dataframe(table, use_container_width=True)
                
                # Column information
                with st.expander("Column Information"):
                    col_info = pd.DataFrame({
                        'Column': table.columns,
                        'Non-null Count': [table[col].count() for col in table.columns],
                        'Data Type': [str(table[col].dtype) for col in table.columns],
                        'Sample Values': [str(table[col].dropna().iloc[0]) if not table[col].dropna().empty else 'N/A' for col in table.columns]
                    })
                    st.dataframe(col_info, use_container_width=True)
            
            # Download options
            st.header("Download Extracted Tables")
            
            # Prepare download files
            download_files = {}
            
            if export_format in ["CSV", "All"]:
                if len(tables) == 1:
                    csv_data = tables[0].to_csv(index=False)
                    download_files["tables.csv"] = csv_data.encode()
                else:
                    for i, table in enumerate(tables, 1):
                        csv_data = table.to_csv(index=False)
                        download_files[f"table_{i}.csv"] = csv_data.encode()
            
            if export_format in ["Excel", "All"]:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    for i, table in enumerate(tables, 1):
                        sheet_name = f'Table_{i}' if len(tables) > 1 else 'Combined_Table'
                        table.to_excel(writer, sheet_name=sheet_name, index=False)
                download_files["tables.xlsx"] = excel_buffer.getvalue()
            
            if export_format in ["HTML", "All"]:
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
                    </style>
                </head>
                <body>
                    <h1>Extracted PDF Tables</h1>
                """
                
                for i, table in enumerate(tables, 1):
                    title = f"Table {i}" if len(tables) > 1 else "Combined Table"
                    html_content += f"""
                    <h2 class="table-header">{title}</h2>
                    {table.to_html(index=False, escape=False)}
                    """
                
                html_content += "</body></html>"
                download_files["tables.html"] = html_content.encode()
            
            # Single file download or zip for multiple files
            if len(download_files) == 1:
                filename, content = next(iter(download_files.items()))
                st.download_button(
                    label=f"Download {filename}",
                    data=content,
                    file_name=filename,
                    mime="application/octet-stream"
                )
            else:
                # Create zip file for multiple downloads
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for filename, content in download_files.items():
                        zip_file.writestr(filename, content)
                
                st.download_button(
                    label="Download All Files (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="extracted_tables.zip",
                    mime="application/zip"
                )
        
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
        
        finally:
            # Clean up temporary file
            Path(tmp_path).unlink(missing_ok=True)
    
    # Instructions
    with st.expander("Instructions & Tips"):
        st.markdown("""
        ### How to use this tool:
        
        1. **Upload your PDF** - The tool supports multi-page PDFs with various table formats
        2. **Configure settings** - Choose whether to merge similar tables and select output format
        3. **Preview tables** - Review extracted tables before downloading
        4. **Download results** - Get your tables in CSV, Excel, or HTML format
        
        ### Tips for best results:
        
        - **Table quality**: PDFs with clear table borders work best
        - **Text-based PDFs**: The tool works better with text-based PDFs rather than scanned images
        - **Complex layouts**: For complex table layouts, try different extraction methods
        - **Multiple formats**: Use "All" format to get tables in multiple formats
        
        ### Extraction Methods:
        
        The tool uses multiple extraction methods automatically:
        - **pdfplumber**: Best for text-based tables
        - **camelot**: Excellent for tables with clear borders
        - **tabula**: Good general-purpose extraction
        
        ### Table Continuity:
        
        The tool automatically detects and combines tables that span multiple pages based on:
        - Column structure similarity
        - Page sequence
        - Table positioning
        """)


if __name__ == "__main__":
    main()
