#!/usr/bin/env python3
"""
Test script to verify the Streamlit compatibility fix
"""

def test_streamlit_compatibility():
    """Test that all required methods exist and work."""
    from pdf_extractor_macos import PDFTableExtractorMacOS
    
    print("🧪 Testing Streamlit compatibility...")
    
    # Test with sample PDF
    extractor = PDFTableExtractorMacOS('test_sample.pdf')
    
    # Test get_extraction_summary method
    try:
        summary = extractor.get_extraction_summary()
        print(f"✅ get_extraction_summary(): {summary}")
    except Exception as e:
        print(f"❌ get_extraction_summary() failed: {e}")
        return False
    
    # Test process_pdf method
    try:
        tables = extractor.process_pdf(merge_similar=True)
        print(f"✅ process_pdf(): Found {len(tables)} tables")
        if tables:
            print(f"   First table shape: {tables[0].shape}")
    except Exception as e:
        print(f"❌ process_pdf() failed: {e}")
        return False
    
    print("🎉 All Streamlit compatibility tests passed!")
    return True

if __name__ == "__main__":
    test_streamlit_compatibility()
