#!/usr/bin/env python3
"""
Convert Czech DBF files from ZIP archive with robust encoding detection and Unicode normalization.

This script processes DBF files containing Czech geographical names, properly handles
Czech diacritics (ř, š, č, ě, ž, ů, etc.), and ensures consistent Unicode representation.

Key features:
- Robust encoding detection with strict validation during detection phase
- Lossless decoding using 'replace' error handling (no silent data loss)  
- Unicode NFC normalization to ensure consistent diacritic representation
- Comprehensive logging of encoding decisions and normalization steps
- Outputs both Excel workbook and individual UTF-8 CSV files
"""

import argparse
import logging
import os
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import dbfread
    import pandas as pd
    from openpyxl import Workbook
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install: pip install dbfread pandas openpyxl")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def detect_encoding(zip_path: str, dbf_filename: str, sample_size: int = 5) -> str:
    """
    Detect the best encoding for a DBF file using strict validation.
    
    Tests multiple encodings on sample data and scores based on Czech diacritics
    vs mojibake patterns. Uses char_decode_errors="strict" so bad candidates
    fail immediately instead of silently dropping bytes.
    
    Args:
        zip_path: Path to ZIP file containing DBF files
        dbf_filename: Name of DBF file within the ZIP
        sample_size: Number of rows to sample for encoding detection
        
    Returns:
        Best encoding name (cp852, cp1250, iso-8859-2)
    """
    encodings_to_test = ['cp852', 'cp1250', 'iso-8859-2']
    
    # Czech diacritics that should be present in correct encoding
    czech_chars = set('áčďéěíňóřšťúůýž')
    # Common mojibake patterns when using wrong encoding
    mojibake_chars = set('ąćęłńśźżĄĆĘŁŃŚŹŻ')
    
    encoding_scores = {}
    
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        # Extract DBF file to temporary file
        with tempfile.NamedTemporaryFile(suffix='.dbf', delete=False) as temp_file:
            temp_file.write(zip_file.read(dbf_filename))
            temp_path = temp_file.name
        
        try:
            for encoding in encodings_to_test:
                try:
                    score = 0
                    samples_tested = 0
                    
                    # Use strict error handling during detection - bad encodings will fail
                    table = dbfread.DBF(temp_path, encoding=encoding, char_decode_errors='strict')
                    
                    for i, record in enumerate(table):
                        if i >= sample_size:
                            break
                            
                        # Examine all string fields in the record
                        for field_name, value in record.items():
                            if isinstance(value, str):
                                # Count Czech diacritics (positive score)
                                czech_count = sum(1 for char in value.lower() if char in czech_chars)
                                # Count mojibake patterns (negative score) 
                                mojibake_count = sum(1 for char in value if char in mojibake_chars)
                                
                                score += czech_count * 2  # Weight Czech chars more
                                score -= mojibake_count * 3  # Penalize mojibake heavily
                        
                        samples_tested += 1
                    
                    encoding_scores[encoding] = score
                    logger.debug(f"Encoding {encoding}: score={score} (tested {samples_tested} rows)")
                    
                except (UnicodeDecodeError, UnicodeError) as e:
                    # Strict decoding failed - this encoding is bad for this file
                    encoding_scores[encoding] = -1000
                    logger.debug(f"Encoding {encoding}: failed strict validation - {e}")
                except Exception as e:
                    logger.debug(f"Encoding {encoding}: failed with error - {e}")
                    encoding_scores[encoding] = -1000
        
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
    
    # Select encoding with highest score
    best_encoding = max(encoding_scores, key=encoding_scores.get)
    best_score = encoding_scores[best_encoding]
    
    # Fallback to cp852 if all encodings scored poorly
    if best_score <= -1000:
        logger.warning(f"All encodings failed strict validation for {dbf_filename}, falling back to cp852")
        best_encoding = 'cp852'
    
    logger.info(f"Selected encoding for {dbf_filename}: {best_encoding} (score: {best_score})")
    return best_encoding


def normalize_unicode_text(text: str) -> str:
    """
    Normalize text to Unicode NFC form.
    
    This converts combining sequences like "u" + U+030A (ring above) to 
    a single precomposed character "ů", ensuring consistent display in
    Excel and CSV files.
    
    Args:
        text: Input text that may contain combining Unicode sequences
        
    Returns:
        Text normalized to NFC form
    """
    if not isinstance(text, str):
        return text
    
    # Normalize to NFC (Canonical Decomposition, followed by Canonical Composition)
    normalized = unicodedata.normalize('NFC', text)
    return normalized


def read_dbf_with_normalization(zip_path: str, dbf_filename: str, encoding: str) -> pd.DataFrame:
    """
    Read DBF file with proper encoding and Unicode normalization.
    
    Uses char_decode_errors="replace" to ensure no data loss - undecodable
    bytes become replacement characters (�) rather than being silently dropped.
    All string values are normalized to Unicode NFC.
    
    Args:
        zip_path: Path to ZIP file containing DBF files  
        dbf_filename: Name of DBF file within the ZIP
        encoding: Encoding to use for reading the file
        
    Returns:
        DataFrame with normalized Unicode text
    """
    logger.info(f"Reading {dbf_filename} with encoding {encoding}")
    
    records = []
    normalization_applied = False
    
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        # Extract DBF file to temporary file
        with tempfile.NamedTemporaryFile(suffix='.dbf', delete=False) as temp_file:
            temp_file.write(zip_file.read(dbf_filename))
            temp_path = temp_file.name
    
    try:
        # Use 'replace' error handling to avoid silent data loss
        table = dbfread.DBF(temp_path, encoding=encoding, char_decode_errors='replace')
        
        for record in table:
            normalized_record = {}
            
            for field_name, value in record.items():
                if isinstance(value, str):
                    # Normalize string values to NFC
                    normalized_value = normalize_unicode_text(value)
                    normalized_record[field_name] = normalized_value
                    
                    # Check if normalization actually changed anything
                    if normalized_value != value:
                        normalization_applied = True
                else:
                    normalized_record[field_name] = value
            
            records.append(normalized_record)
    
    finally:
        # Clean up temporary file
        os.unlink(temp_path)
    
    df = pd.DataFrame(records)
    
    # Apply normalization at DataFrame level as a safeguard
    string_columns = df.select_dtypes(include=['object']).columns
    for col in string_columns:
        df[col] = df[col].astype(str).apply(normalize_unicode_text)
    
    logger.info(f"Normalized strings to NFC for {dbf_filename} ({len(records)} records)")
    if normalization_applied:
        logger.info(f"Unicode normalization was applied to text in {dbf_filename}")
    
    return df


def process_zip_file(zip_path: str, output_dir: str = "output", force_encoding: Optional[str] = None) -> None:
    """
    Process all DBF files in a ZIP archive.
    
    Args:
        zip_path: Path to ZIP file containing DBF files
        output_dir: Directory to save output files
        force_encoding: If provided, use this encoding for all files instead of auto-detection
    """
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Find all DBF files in the ZIP
    dbf_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        for filename in zip_file.namelist():
            if filename.upper().endswith('.DBF'):
                dbf_files.append(filename)
    
    if not dbf_files:
        raise ValueError(f"No DBF files found in {zip_path}")
    
    logger.info(f"Found {len(dbf_files)} DBF files in {zip_path}")
    
    # Process each DBF file
    dataframes = {}
    encoding_summary = {}
    
    for dbf_filename in dbf_files:
        try:
            # Determine encoding
            if force_encoding:
                encoding = force_encoding
                logger.info(f"Using forced encoding {encoding} for {dbf_filename}")
            else:
                encoding = detect_encoding(zip_path, dbf_filename)
            
            encoding_summary[dbf_filename] = encoding
            
            # Read and normalize the DBF file
            df = read_dbf_with_normalization(zip_path, dbf_filename, encoding)
            
            # Store with clean name (without .DBF extension)
            clean_name = Path(dbf_filename).stem
            dataframes[clean_name] = df
            
            logger.info(f"Successfully processed {dbf_filename}: {len(df)} records")
            
        except Exception as e:
            logger.error(f"Failed to process {dbf_filename}: {e}")
            continue
    
    if not dataframes:
        raise RuntimeError("Failed to process any DBF files")
    
    # Create Excel workbook
    excel_path = Path(output_dir) / "czech_names.xlsx"
    logger.info(f"Creating Excel workbook: {excel_path}")
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for sheet_name, df in dataframes.items():
            # Excel sheet names have length limit
            safe_sheet_name = sheet_name[:31] if len(sheet_name) > 31 else sheet_name
            df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            logger.info(f"Added sheet '{safe_sheet_name}' with {len(df)} records")
    
    # Create individual CSV files
    csv_dir = Path(output_dir) / "csv"
    csv_dir.mkdir(exist_ok=True)
    
    for name, df in dataframes.items():
        csv_path = csv_dir / f"{name}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"Created CSV: {csv_path} ({len(df)} records)")
    
    # Log encoding summary
    logger.info("=== ENCODING SUMMARY ===")
    for dbf_file, encoding in encoding_summary.items():
        logger.info(f"{dbf_file}: {encoding}")
    
    logger.info(f"Processing complete. Output saved to {output_dir}/")
    logger.info(f"Excel file: {excel_path}")
    logger.info(f"CSV files: {csv_dir}/")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert Czech DBF files with proper diacritic handling and Unicode normalization'
    )
    parser.add_argument('zip_path', help='Path to ZIP file containing DBF files')
    parser.add_argument('--output', '-o', default='output', help='Output directory (default: output)')
    parser.add_argument(
        '--encoding', 
        choices=['cp852', 'cp1250', 'iso-8859-2'],
        help='Force specific encoding for all files (overrides auto-detection)'
    )
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        process_zip_file(args.zip_path, args.output, args.encoding)
        logger.info("Conversion completed successfully!")
        
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()