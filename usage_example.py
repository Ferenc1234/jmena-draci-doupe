#!/usr/bin/env python3
"""
Usage example demonstrating the key features of convert_drd_names.py
"""

import subprocess
import sys
import os

def run_examples():
    """Run example conversions to demonstrate the features."""
    
    zip_file = "jmena(1).zip"
    if not os.path.exists(zip_file):
        print(f"Error: {zip_file} not found")
        return
    
    print("=== Czech DBF Converter Usage Examples ===\n")
    
    # Example 1: Automatic encoding detection
    print("1. Automatic encoding detection (recommended):")
    print(f"   python convert_drd_names.py '{zip_file}'")
    print("   → Detects best encoding for each file, applies Unicode NFC normalization")
    print("   → Creates output/czech_names.xlsx and output/csv/*.csv\n")
    
    # Example 2: Forced encoding
    print("2. Force specific encoding:")
    print(f"   python convert_drd_names.py '{zip_file}' --encoding cp852")
    print("   → Uses CP852 for all files (overrides auto-detection)\n")
    
    # Example 3: Custom output directory
    print("3. Custom output directory:")
    print(f"   python convert_drd_names.py '{zip_file}' --output my_output")
    print("   → Saves to my_output/ instead of output/\n")
    
    # Example 4: Verbose logging
    print("4. Verbose logging (see encoding decisions):")
    print(f"   python convert_drd_names.py '{zip_file}' --verbose")
    print("   → Shows detailed encoding detection scores and normalization steps\n")
    
    print("Key benefits:")
    print("• Czech diacritics (ř, š, č, ě, ž, ů, etc.) are preserved correctly")
    print("• Unicode normalization ensures consistent display in Excel/CSV") 
    print("• No silent data loss - undecodable bytes become visible (�)")
    print("• Comprehensive logging shows encoding decisions per file")
    print("• Multiple output formats for different use cases")

def demonstrate_normalization():
    """Show Unicode normalization in action."""
    
    import unicodedata
    from convert_drd_names import normalize_unicode_text
    
    print("\n=== Unicode Normalization Demo ===")
    
    # Create text with combining characters (like Excel might produce)
    combining_text = "ku" + "\u030A" + "n"  # ku + ring above + n = kůň  
    normalized = normalize_unicode_text(combining_text)
    
    print(f"Text with combining chars: {repr(combining_text)} → '{combining_text}'")
    print(f"After NFC normalization:  {repr(normalized)} → '{normalized}'")
    print(f"Length before: {len(combining_text)}, after: {len(normalized)}")
    print(f"Now displays consistently in Excel and CSVs!")

if __name__ == '__main__':
    run_examples()
    demonstrate_normalization()