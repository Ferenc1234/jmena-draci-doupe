#!/usr/bin/env python3
"""
Test script to validate Unicode normalization and encoding behavior.
"""
import unicodedata
import tempfile
import os
from convert_drd_names import normalize_unicode_text

def test_unicode_normalization():
    """Test Unicode NFC normalization."""
    print("=== Unicode Normalization Tests ===")
    
    # Test combining characters -> precomposed
    test_cases = [
        ('u\u030A', 'ů'),  # u + ring above -> ů
        ('a\u0301', 'á'),  # a + acute -> á 
        ('e\u030C', 'ě'),  # e + caron -> ě
        ('c\u030C', 'č'),  # c + caron -> č
        ('r\u030C', 'ř'),  # r + caron -> ř
        ('s\u030C', 'š'),  # s + caron -> š
    ]
    
    for combining, expected in test_cases:
        normalized = normalize_unicode_text(combining)
        success = normalized == expected
        print(f"  {repr(combining)} -> {repr(normalized)} (expected {repr(expected)}) ✓" if success else f"  {repr(combining)} -> {repr(normalized)} (expected {repr(expected)}) ✗")

def test_encoding_behavior():
    """Test encoding error handling behavior."""
    print("\n=== Encoding Error Handling Tests ===")
    
    # Create test data with mixed content
    test_content = b"Valid text \xff\xfe Invalid bytes more text"
    
    # Test 'ignore' vs 'replace' behavior
    ignore_result = test_content.decode('utf-8', errors='ignore')
    replace_result = test_content.decode('utf-8', errors='replace')
    
    print(f"Original bytes: {test_content}")
    print(f"With 'ignore': {repr(ignore_result)}")
    print(f"With 'replace': {repr(replace_result)}")
    print(f"'ignore' loses data: {b'\\xff\\xfe' not in ignore_result.encode('utf-8', errors='ignore')}")
    print(f"'replace' preserves indication: {'�' in replace_result}")

def test_czech_diacritics():
    """Test that Czech diacritics are preserved."""
    print("\n=== Czech Diacritics Preservation Test ===")
    
    czech_text = "Příliš žluťoučký kůň úpěl ďábelské ódy"
    normalized = normalize_unicode_text(czech_text)
    
    print(f"Original: {czech_text}")
    print(f"Normalized: {normalized}")
    print(f"Preserved correctly: {czech_text == normalized}")
    
    # Count diacritics
    czech_chars = set('áčďéěíňóřšťúůýž')
    diacritic_count = sum(1 for char in normalized.lower() if char in czech_chars)
    print(f"Diacritic characters found: {diacritic_count}")

if __name__ == '__main__':
    test_unicode_normalization()
    test_encoding_behavior() 
    test_czech_diacritics()
    print("\n=== All tests completed ===")