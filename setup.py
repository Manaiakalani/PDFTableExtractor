#!/usr/bin/env python3
"""
Setup script for PDF Table Extractor

This script helps set up the environment and install all necessary dependencies.
"""

import subprocess
import sys
import platform
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error during {description}: {e}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def install_system_dependencies():
    """Install system-level dependencies."""
    system = platform.system().lower()
    
    print(f"🖥️  Detected system: {system}")
    
    if system == "darwin":  # macOS
        print("Installing Ghostscript via Homebrew...")
        if not run_command("brew --version", "Checking Homebrew"):
            print("❌ Homebrew not found. Please install Homebrew first:")
            print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            return False
        
        return run_command("brew install ghostscript", "Installing Ghostscript")
    
    elif system == "linux":
        # Try different package managers
        if run_command("which apt-get", "Checking apt-get"):
            return run_command("sudo apt-get update && sudo apt-get install -y ghostscript", 
                             "Installing Ghostscript via apt")
        elif run_command("which yum", "Checking yum"):
            return run_command("sudo yum install -y ghostscript", 
                             "Installing Ghostscript via yum")
        elif run_command("which pacman", "Checking pacman"):
            return run_command("sudo pacman -S ghostscript", 
                             "Installing Ghostscript via pacman")
        else:
            print("❌ Could not detect package manager. Please install ghostscript manually.")
            return False
    
    elif system == "windows":
        print("⚠️  Please install Ghostscript manually on Windows:")
        print("   1. Go to: https://www.ghostscript.com/download/gsdnld.html")
        print("   2. Download and install the Windows version")
        print("   3. Add Ghostscript to your PATH")
        return True
    
    else:
        print(f"⚠️  Unknown system: {system}")
        print("Please install ghostscript manually for your system.")
        return True


def install_python_dependencies():
    """Install Python dependencies."""
    print("🐍 Installing Python dependencies...")
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", 
                      "Upgrading pip"):
        return False
    
    # Install requirements
    requirements_path = Path(__file__).parent / "requirements.txt"
    if requirements_path.exists():
        return run_command(f"{sys.executable} -m pip install -r {requirements_path}", 
                         "Installing Python packages")
    else:
        # Install packages individually if requirements.txt is missing
        packages = [
            "tabula-py>=2.9.0",
            "pandas>=1.5.0",
            "openpyxl>=3.0.0",
            "camelot-py[cv]>=0.11.0",
            "pdfplumber>=0.10.0",
            "beautifulsoup4>=4.11.0",
            "streamlit>=1.28.0",
            "lxml>=4.9.0",
            "Pillow>=9.0.0",
            "opencv-python>=4.5.0"
        ]
        
        for package in packages:
            if not run_command(f"{sys.executable} -m pip install {package}", 
                             f"Installing {package}"):
                print(f"⚠️  Failed to install {package}")
        
        return True


def verify_installation():
    """Verify that all components are installed correctly."""
    print("🔍 Verifying installation...")
    
    # Test imports
    test_imports = [
        ("tabula", "tabula"),
        ("camelot", "camelot"),
        ("pdfplumber", "pdfplumber"),
        ("pandas", "pd"),
        ("openpyxl", "openpyxl"),
        ("streamlit", "st")
    ]
    
    failed_imports = []
    
    for module_name, import_name in test_imports:
        try:
            __import__(module_name)
            print(f"✅ {module_name} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {module_name}: {e}")
            failed_imports.append(module_name)
    
    if failed_imports:
        print(f"\n❌ Some imports failed: {', '.join(failed_imports)}")
        print("Try running: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies verified successfully!")
    return True


def create_sample_pdf():
    """Create a sample PDF with tables for testing."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        
        # Sample data
        data1 = [
            ['Product', 'Quantity', 'Price', 'Total'],
            ['Widget A', '10', '$5.00', '$50.00'],
            ['Widget B', '5', '$10.00', '$50.00'],
            ['Widget C', '15', '$3.00', '$45.00']
        ]
        
        data2 = [
            ['Month', 'Sales', 'Profit', 'Growth'],
            ['January', '$1000', '$200', '5%'],
            ['February', '$1200', '$240', '20%'],
            ['March', '$1100', '$220', '-8%']
        ]
        
        # Create PDF
        doc = SimpleDocTemplate("sample_tables.pdf", pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph("Sample Document with Tables", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # First table
        elements.append(Paragraph("Product Inventory", styles['Heading2']))
        t1 = Table(data1)
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 30))
        
        # Second table
        elements.append(Paragraph("Monthly Sales Report", styles['Heading2']))
        t2 = Table(data2)
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t2)
        
        doc.build(elements)
        print("✅ Created sample_tables.pdf for testing")
        return True
        
    except ImportError:
        print("⚠️  reportlab not installed. Cannot create sample PDF.")
        print("Install with: pip install reportlab")
        return False
    except Exception as e:
        print(f"❌ Error creating sample PDF: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 PDF Table Extractor Setup")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install system dependencies
    print("\n📋 Installing system dependencies...")
    install_system_dependencies()
    
    # Install Python dependencies
    print("\n📋 Installing Python dependencies...")
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Verify installation
    print("\n📋 Verifying installation...")
    if not verify_installation():
        print("❌ Installation verification failed")
        sys.exit(1)
    
    # Create sample PDF
    print("\n📋 Creating sample PDF...")
    create_sample_pdf()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Test with sample PDF: python pdf_table_extractor.py sample_tables.pdf")
    print("2. Launch web interface: streamlit run streamlit_app.py")
    print("3. See example_usage.py for more examples")


if __name__ == "__main__":
    main()
