#!/bin/bash
# Quick Start Script for PDF Table Extractor

echo "🚀 PDF Table Extractor - Quick Start"
echo "===================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed"
    exit 1
fi

echo "✅ pip3 found"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Check installation
echo ""
echo "🔍 Testing installation..."
python3 test_extractor.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "📋 Available options:"
    echo "   1. Command line: python3 pdf_table_extractor.py your_file.pdf"
    echo "   2. Web interface: streamlit run streamlit_app.py"
    echo "   3. Jupyter notebook: jupyter notebook PDF_Table_Extraction.ipynb"
    echo "   4. See examples: python3 example_usage.py"
    echo ""
    echo "💡 For help: python3 pdf_table_extractor.py --help"
else
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi
