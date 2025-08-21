#!/usr/bin/env python3
"""
Test script for PDF Table Extractor

This script runs basic tests to ensure the PDF table extraction tool works correctly.
"""

import sys
import traceback
from pathlib import Path
import pandas as pd

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        import tabula
        print("✅ tabula-py imported")
    except ImportError as e:
        print(f"❌ tabula-py import failed: {e}")
        return False
    
    try:
        import camelot
        print("✅ camelot imported")
    except ImportError as e:
        print(f"❌ camelot import failed: {e}")
        return False
    
    try:
        import pdfplumber
        print("✅ pdfplumber imported")
    except ImportError as e:
        print(f"❌ pdfplumber import failed: {e}")
        return False
    
    try:
        from pdf_table_extractor import PDFTableExtractor
        print("✅ PDFTableExtractor imported")
    except ImportError as e:
        print(f"❌ PDFTableExtractor import failed: {e}")
        return False
    
    return True


def create_test_pdf():
    """Create a simple test PDF with tables."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        from reportlab.lib import colors
        
        # Create simple test data
        data = [
            ['Name', 'Age', 'City'],
            ['Alice', '25', 'New York'],
            ['Bob', '30', 'Los Angeles'],
            ['Charlie', '35', 'Chicago']
        ]
        
        # Create PDF
        doc = SimpleDocTemplate("test_table.pdf", pagesize=letter)
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        doc.build([table])
        print("✅ Created test_table.pdf")
        return "test_table.pdf"
        
    except ImportError:
        print("⚠️  reportlab not available, cannot create test PDF")
        return None
    except Exception as e:
        print(f"❌ Error creating test PDF: {e}")
        return None


def test_extraction():
    """Test table extraction functionality."""
    print("\n🧪 Testing table extraction...")
    
    # Create test PDF
    test_pdf = create_test_pdf()
    if not test_pdf:
        print("❌ Cannot test without PDF file")
        return False
    
    try:
        from pdf_table_extractor import PDFTableExtractor
        
        # Test extraction
        extractor = PDFTableExtractor(test_pdf)
        tables = extractor.extract_all_tables()
        
        if not tables:
            print("❌ No tables extracted")
            return False
        
        print(f"✅ Extracted {len(tables)} tables")
        
        # Test processing
        combined_tables = extractor.process_pdf(
            merge_similar=True,
            output_format='csv',
            output_path='test_output'
        )
        
        if not combined_tables:
            print("❌ No tables after processing")
            return False
        
        print(f"✅ Processed into {len(combined_tables)} final tables")
        
        # Verify output files
        csv_file = Path("test_output.csv")
        if csv_file.exists():
            print("✅ CSV export successful")
            
            # Read back and verify
            df = pd.read_csv(csv_file)
            if not df.empty:
                print(f"✅ CSV contains {len(df)} rows")
            else:
                print("❌ CSV file is empty")
                return False
        else:
            print("❌ CSV file not created")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Extraction test failed: {e}")
        traceback.print_exc()
        return False


def test_streamlit_app():
    """Test that the Streamlit app can be imported."""
    print("\n🧪 Testing Streamlit app...")
    
    try:
        import streamlit
        print("✅ Streamlit available")
        
        # Check if app file exists
        app_file = Path("streamlit_app.py")
        if app_file.exists():
            print("✅ Streamlit app file exists")
            return True
        else:
            print("❌ Streamlit app file not found")
            return False
            
    except ImportError:
        print("⚠️  Streamlit not available (optional)")
        return True  # Not critical for basic functionality


def cleanup_test_files():
    """Clean up test files."""
    test_files = [
        "test_table.pdf",
        "test_output.csv",
        "test_output.xlsx",
        "test_output.html",
        "pdf_extraction.log"
    ]
    
    for file in test_files:
        file_path = Path(file)
        if file_path.exists():
            file_path.unlink()
            print(f"🗑️  Cleaned up {file}")


def main():
    """Run all tests."""
    print("🧪 PDF Table Extractor - Test Suite")
    print("=" * 50)
    
    # Track test results
    test_results = {}
    
    # Test imports
    test_results['imports'] = test_imports()
    
    # Test extraction (only if imports work)
    if test_results['imports']:
        test_results['extraction'] = test_extraction()
    else:
        test_results['extraction'] = False
        print("⏭️  Skipping extraction test due to import failures")
    
    # Test Streamlit app
    test_results['streamlit'] = test_streamlit_app()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.capitalize()}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The PDF Table Extractor is ready to use.")
        print("\n📋 Quick start:")
        print("   • Command line: python pdf_table_extractor.py your_file.pdf")
        print("   • Web interface: streamlit run streamlit_app.py")
        print("   • Jupyter notebook: Open PDF_Table_Extraction.ipynb")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        print("💡 Try running: python setup.py")
    
    # Cleanup
    cleanup_test_files()
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
