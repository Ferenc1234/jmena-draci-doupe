#!/usr/bin/env python3
"""
Download MorfFlex CZ forms dictionary for diacritization.

This script downloads the MorfFlex Czech dictionary with robust error handling,
verification, and caching support for CI environments.
"""

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path


def run_curl_download(url: str, output_path: str) -> bool:
    """
    Download file using curl with robust retry and timeout settings.
    
    Returns:
        True if download successful, False otherwise
    """
    curl_cmd = [
        'curl', '-L', '--fail', '--retry', '5', '--retry-all-errors',
        '--connect-timeout', '20', '--max-time', '300',
        '--output', output_path, url
    ]
    
    print(f"Downloading MorfFlex from: {url}")
    print(f"Command: {' '.join(curl_cmd)}")
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=400)
        if result.returncode == 0:
            print("✓ Download completed successfully")
            return True
        else:
            print(f"✗ Download failed with exit code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ Download timed out")
        return False
    except Exception as e:
        print(f"✗ Download failed with exception: {e}")
        return False


def verify_download(file_path: str) -> tuple[bool, str]:
    """
    Verify the downloaded file is valid and reasonable size.
    
    Returns:
        Tuple of (is_valid, checksum)
    """
    if not os.path.exists(file_path):
        print(f"✗ File does not exist: {file_path}")
        return False, ""
    
    # Check file size (should be > 10 MB for MorfFlex forms)
    file_size = os.path.getsize(file_path)
    min_size = 10 * 1024 * 1024  # 10 MB
    
    print(f"File size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")
    
    if file_size < min_size:
        print(f"✗ File too small (< {min_size:,} bytes), likely corrupted or incomplete")
        return False, ""
    
    # Calculate SHA256 checksum
    print("Calculating SHA256 checksum...")
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        checksum = sha256_hash.hexdigest()
        print(f"✓ SHA256: {checksum}")
        return True, checksum
    except Exception as e:
        print(f"✗ Error calculating checksum: {e}")
        return False, ""


def main():
    parser = argparse.ArgumentParser(
        description="Download MorfFlex CZ forms dictionary with robust error handling"
    )
    parser.add_argument(
        "--output", "-o",
        default="diacritics/morfflex.tsv",
        help="Output file path (default: diacritics/morfflex.tsv)"
    )
    parser.add_argument(
        "--url",
        default="https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11858/00-097C-0000-0023-1B22-8/morphodita-czech-forms-1.1.tsv.gz",
        help="URL to download MorfFlex forms from"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force download even if file already exists"
    )
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_dir = output_path.parent
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if file already exists and is valid (unless force is specified)
    if not args.force and output_path.exists():
        print(f"File already exists: {output_path}")
        is_valid, checksum = verify_download(str(output_path))
        if is_valid:
            print("✓ Existing file is valid, skipping download")
            # Output checksum for caching
            print(f"CACHE_KEY={checksum}")
            return 0
        else:
            print("Existing file is invalid, will re-download")
    
    # Determine if we need to decompress
    is_compressed = args.url.endswith('.gz')
    download_path = str(output_path) + '.gz' if is_compressed else str(output_path)
    
    print("="*60)
    print("MorfFlex Download")
    print("="*60)
    
    # Download the file
    success = run_curl_download(args.url, download_path)
    
    if not success:
        print("\n" + "="*60)
        print("WARNING: MorfFlex download failed; running overrides-only")
        print("="*60)
        # Set environment variable for CI
        if 'GITHUB_ENV' in os.environ:
            with open(os.environ['GITHUB_ENV'], 'a') as f:
                f.write('MORFFLEX_DEGRADED=true\n')
        os.environ['MORFFLEX_DEGRADED'] = 'true'
        return 1
    
    # Decompress if needed
    if is_compressed:
        print("Decompressing...")
        try:
            import gzip
            with gzip.open(download_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            os.remove(download_path)
            print("✓ Decompression completed")
        except Exception as e:
            print(f"✗ Decompression failed: {e}")
            return 1
    
    # Verify the final file
    is_valid, checksum = verify_download(str(output_path))
    
    if not is_valid:
        print("\n" + "="*60)
        print("WARNING: MorfFlex download failed; running overrides-only")
        print("="*60)
        # Set environment variable for CI
        if 'GITHUB_ENV' in os.environ:
            with open(os.environ['GITHUB_ENV'], 'a') as f:
                f.write('MORFFLEX_DEGRADED=true\n')
        os.environ['MORFFLEX_DEGRADED'] = 'true'
        return 1
    
    print("\n" + "="*60)
    print("✓ MorfFlex download completed successfully")
    print("="*60)
    print(f"File: {output_path}")
    print(f"Size: {os.path.getsize(output_path):,} bytes")
    print(f"SHA256: {checksum}")
    
    # Output checksum for caching
    print(f"CACHE_KEY={checksum}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())