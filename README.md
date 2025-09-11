# jmena-draci-doupe

A tool for converting Dračí doupě (Dragon's Den RPG) name databases from DBF files to Excel and CSV formats with proper Czech diacritics handling.

## Overview

This repository processes DBF files containing Czech geographical and character names for the Dračí doupě RPG system. The main challenge is preserving Czech diacritics (ř, š, č, ž, ě, etc.) which can become garbled (mojibake) when the wrong text encoding is used.

## Files

- `convert_drd_names.py` - Main conversion script with automatic encoding detection
- `jmena(1).zip` - Source DBF files with Czech name databases
- `.github/workflows/convert-drd-jmena.yml` - GitHub Actions workflow for automated conversion

## Usage

### Local Usage

```bash
# Install dependencies
pip install dbfread openpyxl pandas chardet

# Convert with automatic encoding detection (recommended)
python convert_drd_names.py "jmena(1).zip"

# Force a specific encoding if auto-detection fails
python convert_drd_names.py "jmena(1).zip" --encoding cp852

# Specify custom output directory
python convert_drd_names.py "jmena(1).zip" --output-dir my_output
```

### GitHub Actions

The repository includes an automated workflow that:

1. **Triggers automatically** on pushes and pull requests to main branch
2. **Manual dispatch** available with optional parameters:
   - `encoding`: Force specific encoding (cp852, cp1250, iso-8859-2)
   - `zip_path`: Custom path to ZIP file (default: jmena(1).zip)

To run manually:
1. Go to **Actions** tab in GitHub
2. Select **Convert DRD Names** workflow  
3. Click **Run workflow**
4. Optionally specify encoding or ZIP path

## Output

The conversion produces:

- **Excel workbook** (`drd_names.xlsx`) with one sheet per DBF file
- **Individual CSV files** for each DBF table (UTF-8 encoded)
- **Encoding summary** in the logs showing which encoding was used for each file

## Troubleshooting Czech Diacritics

### Common Issues

**Problem**: Characters like ř, š, č, ě appear as symbols like Ą, Ć, etc.
- **Cause**: Wrong text encoding (usually ISO-8859-2 instead of CP852)
- **Solution**: Use `--encoding cp852` to force correct encoding

**Problem**: Some files decode correctly, others don't
- **Cause**: Mixed encodings in different DBF files  
- **Solution**: Let auto-detection handle each file individually

### Encoding Options

| Encoding | When to Use | Common Issues |
|----------|-------------|---------------|
| `cp852` | **Recommended** - Most Czech DBF files | None usually |
| `cp1250` | Windows Central European encoding | May fail on some files |
| `iso-8859-2` | Latin-2 Central European | Creates mojibake (Ą instead of í) |

### Example Run

```
$ python convert_drd_names.py "jmena(1).zip"
Converting DBF files from: jmena(1).zip
Output directory: output
Using automatic encoding detection

Processing MESTA.DBF...
  Detected encoding: cp852 (score: 0.047, method: czech_scoring)
  Loaded 8607 records with 8 columns
  Saved to Excel sheet 'MESTA' and output/MESTA.csv

============================================================
ENCODING SUMMARY  
============================================================
MESTA.DBF            -> cp852
JMENA.DBF            -> cp852
PRIJMENI.DBF         -> cp852
...
```

### Manual Override Examples

**Force CP852 for all files:**
```bash
python convert_drd_names.py "jmena(1).zip" --encoding cp852
```

**Via GitHub Actions:**
1. Actions → Convert DRD Names → Run workflow
2. Set `encoding` input to `cp852`

### Verifying Output

Check for proper Czech characters in the output:
```bash
# Look for Czech diacritics in CSV
grep "ř\|š\|č\|ě\|ž" output/MESTA.csv

# Should show: Breclavím, Českých, etc.
# NOT: BreclavĄm, ČeskĄch (mojibake)
```

## Technical Details

The conversion script:

1. **Auto-detects encoding** by testing sample records from each DBF file
2. **Scores encodings** based on Czech diacritics vs mojibake patterns  
3. **Falls back to CP852** if detection fails
4. **Processes all 30 DBF files** in the ZIP archive
5. **Outputs UTF-8** CSV and Excel files for maximum compatibility

### Encoding Detection Algorithm

1. Try chardet library on raw file bytes
2. Test each encoding (cp852, cp1250, iso-8859-2) on sample records
3. Score based on:
   - Presence of valid Czech diacritics (áčďéěíňóřšťúůýž)
   - Absence of mojibake patterns (Ą, Ć, etc.)
4. Select encoding with highest score