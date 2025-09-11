#!/usr/bin/env python3
"""
Convert DBF files to Excel and CSV with proper Czech diacritics handling.

This script processes DBF files from Dračí doupě name databases, automatically
detects the proper encoding to preserve Czech diacritics, and outputs clean
Excel workbooks and UTF-8 CSV files.
"""

import argparse
import csv
import os
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import pandas as pd
    from dbfread import DBF
    import openpyxl
    import chardet
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install: pip install dbfread openpyxl pandas chardet")
    sys.exit(1)


def score_czech_encoding(text_sample: str) -> float:
    """
    Score text sample for Czech character quality.
    
    Returns a score from 0-1 where:
    - Higher score = better Czech diacritics
    - Lower score = more mojibake/encoding issues
    """
    if not text_sample:
        return 0.0
    
    # Common Czech diacritics
    czech_chars = "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"
    
    # Common mojibake patterns when Czech is wrongly decoded
    mojibake_patterns = [
        "Ą", "Ć", "Ę", "Ł", "Ń", "Ś", "Ź", "Ż",  # Polish chars from wrong encoding
        "â", "ã", "ä", "å", "æ", "ç", "è", "ê", "ë",  # Western European mojibake
        "¡", "¢", "£", "¤", "¥", "¦", "§", "¨", "©",  # Symbol mojibake
        "°", "±", "²", "³", "´", "µ", "¶", "·", "¸", "¹"  # More symbol mojibake
    ]
    
    # Count good Czech characters vs mojibake
    czech_count = sum(1 for char in text_sample if char in czech_chars)
    mojibake_count = sum(1 for char in text_sample if char in mojibake_patterns)
    total_chars = len(text_sample)
    
    if total_chars == 0:
        return 0.0
    
    # Calculate score: Czech characters boost, mojibake reduces
    czech_ratio = czech_count / total_chars
    mojibake_penalty = mojibake_count / total_chars
    
    # Score formula: Czech boost minus mojibake penalty, normalized
    score = max(0.0, (czech_ratio * 2) - (mojibake_penalty * 3))
    return min(1.0, score)


def detect_dbf_encoding(dbf_path: str, sample_size: int = 100) -> Tuple[str, float, str]:
    """
    Detect the best encoding for a DBF file.
    
    Returns:
        Tuple of (best_encoding, confidence_score, detection_method)
    """
    encodings_to_try = ['cp852', 'cp1250', 'iso-8859-2']
    
    # First, try chardet on raw file bytes
    try:
        with open(dbf_path, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB
        detected = chardet.detect(raw_data)
        chardet_encoding = detected.get('encoding', '').lower()
        
        # Map chardet results to our target encodings
        if chardet_encoding in ['iso-8859-1', 'iso-8859-2']:
            encodings_to_try.insert(0, 'iso-8859-2')
        elif 'cp' in chardet_encoding or 'windows' in chardet_encoding:
            encodings_to_try.insert(0, 'cp1250')
    except Exception:
        pass
    
    best_encoding = 'cp852'  # Default fallback
    best_score = 0.0
    best_method = 'fallback'
    
    # Try each encoding and score the results
    for encoding in encodings_to_try:
        try:
            table = DBF(dbf_path, encoding=encoding, ignore_missing_memofile=True)
            
            # Collect sample text from first records
            sample_texts = []
            record_count = 0
            
            for record in table:
                if record_count >= sample_size:
                    break
                
                # Collect all string values from the record
                for field_name, value in record.items():
                    if isinstance(value, str) and len(value.strip()) > 0:
                        sample_texts.append(value.strip())
                
                record_count += 1
            
            if sample_texts:
                # Score the combined sample
                combined_text = ' '.join(sample_texts)
                score = score_czech_encoding(combined_text)
                
                if score > best_score:
                    best_score = score
                    best_encoding = encoding
                    best_method = 'czech_scoring'
                    
        except Exception as e:
            # This encoding failed completely
            continue
    
    return best_encoding, best_score, best_method


def convert_dbf_to_dataframe(dbf_path: str, encoding: str) -> pd.DataFrame:
    """Convert a DBF file to a pandas DataFrame with specified encoding."""
    try:
        table = DBF(dbf_path, encoding=encoding, ignore_missing_memofile=True)
        records = []
        for record in table:
            records.append(dict(record))
        return pd.DataFrame(records)
    except Exception as e:
        print(f"Error converting {dbf_path} with encoding {encoding}: {e}")
        raise


def process_dbf_files(
    zip_path: str,
    output_dir: str = "output",
    force_encoding: Optional[str] = None
) -> Dict[str, str]:
    """
    Process all DBF files in a ZIP archive.
    
    Returns:
        Dictionary mapping DBF filenames to their detected/used encodings
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract ZIP to temporary directory
    temp_dir = Path(output_dir) / "temp_dbf"
    temp_dir.mkdir(exist_ok=True)
    
    encoding_summary = {}
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # Extract all DBF files
            dbf_files = [name for name in zip_file.namelist() if name.upper().endswith('.DBF')]
            
            if not dbf_files:
                print(f"No DBF files found in {zip_path}")
                return encoding_summary
            
            print(f"Found {len(dbf_files)} DBF files in {zip_path}")
            
            # Extract DBF files
            for dbf_name in dbf_files:
                zip_file.extract(dbf_name, temp_dir)
            
            # Create Excel workbook
            excel_path = Path(output_dir) / "drd_names.xlsx"
            
            with pd.ExcelWriter(excel_path, engine='openpyxl') as excel_writer:
                
                for dbf_name in sorted(dbf_files):
                    dbf_path = temp_dir / dbf_name
                    base_name = Path(dbf_name).stem
                    
                    print(f"\nProcessing {dbf_name}...")
                    
                    # Determine encoding
                    if force_encoding:
                        encoding = force_encoding
                        detection_method = 'manual_override'
                        score = 1.0
                        print(f"  Using forced encoding: {encoding}")
                    else:
                        encoding, score, detection_method = detect_dbf_encoding(str(dbf_path))
                        print(f"  Detected encoding: {encoding} (score: {score:.3f}, method: {detection_method})")
                    
                    encoding_summary[dbf_name] = encoding
                    
                    # Convert to DataFrame
                    try:
                        df = convert_dbf_to_dataframe(str(dbf_path), encoding)
                        
                        if df.empty:
                            print(f"  Warning: {dbf_name} is empty")
                            continue
                        
                        print(f"  Loaded {len(df)} records with {len(df.columns)} columns")
                        
                        # Add to Excel workbook
                        sheet_name = base_name[:31]  # Excel sheet name limit
                        df.to_excel(excel_writer, sheet_name=sheet_name, index=False)
                        
                        # Save as CSV
                        csv_path = Path(output_dir) / f"{base_name}.csv"
                        df.to_csv(csv_path, index=False, encoding='utf-8')
                        
                        print(f"  Saved to Excel sheet '{sheet_name}' and {csv_path}")
                        
                    except Exception as e:
                        print(f"  Error processing {dbf_name}: {e}")
                        encoding_summary[dbf_name] += f" (ERROR: {e})"
            
            print(f"\nExcel workbook saved to: {excel_path}")
            
    finally:
        # Clean up temporary files
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    return encoding_summary


def main():
    parser = argparse.ArgumentParser(
        description="Convert DBF files to Excel and CSV with proper Czech diacritics"
    )
    parser.add_argument(
        "zip_file",
        help="Path to ZIP file containing DBF files"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="output",
        help="Output directory (default: output)"
    )
    parser.add_argument(
        "--encoding", "-e",
        choices=['cp852', 'cp1250', 'iso-8859-2'],
        help="Force specific encoding for all DBF files (overrides auto-detection)"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.zip_file):
        print(f"Error: ZIP file not found: {args.zip_file}")
        sys.exit(1)
    
    print(f"Converting DBF files from: {args.zip_file}")
    print(f"Output directory: {args.output_dir}")
    
    if args.encoding:
        print(f"Forced encoding: {args.encoding}")
    else:
        print("Using automatic encoding detection")
    
    try:
        encoding_summary = process_dbf_files(
            args.zip_file,
            args.output_dir,
            args.encoding
        )
        
        print("\n" + "="*60)
        print("ENCODING SUMMARY")
        print("="*60)
        for dbf_name, encoding in encoding_summary.items():
            print(f"{dbf_name:20s} -> {encoding}")
        
        print("\nConversion completed successfully!")
        
    except Exception as e:
        print(f"\nError during conversion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()