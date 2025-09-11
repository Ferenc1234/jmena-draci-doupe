# jmena-draci-doupe

Czech DBF File Converter with robust encoding detection and Unicode normalization.

This tool converts Czech geographical DBF files with proper diacritic handling, ensuring characters like **ř**, **š**, **č**, **ě**, **ž**, **ů** are preserved correctly without mojibake.

## Features

- **🔧 Robust Encoding Detection**: Automatically detects the best encoding (CP852, CP1250, ISO-8859-2) for each DBF file
- **🛡️ Lossless Decoding**: Uses 'replace' error handling instead of 'ignore' to prevent silent data loss 
- **🔤 Unicode NFC Normalization**: Converts combining sequences to single characters for consistent display
- **📊 Multiple Output Formats**: Excel workbook + individual UTF-8 CSV files
- **📝 Comprehensive Logging**: Shows encoding decisions and normalization status per file
- **⚙️ Manual Override**: Force specific encoding when needed

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Automatic Detection (Recommended)
```bash
python convert_drd_names.py "jmena(1).zip"
```

### Force Specific Encoding
```bash
python convert_drd_names.py "jmena(1).zip" --encoding cp852
```

### Custom Output Directory  
```bash
python convert_drd_names.py "jmena(1).zip" --output my_results
```

### Verbose Logging
```bash
python convert_drd_names.py "jmena(1).zip" --verbose
```

## Output

- **Excel file**: `output/czech_names.xlsx` - Single file with one sheet per DBF table
- **CSV files**: `output/csv/*.csv` - Individual UTF-8 encoded CSV files
- **Logs**: Encoding selection and normalization status for each file

## Key Improvements

This implementation addresses common issues with Czech text processing:

1. **No Silent Data Loss**: Uses `char_decode_errors="replace"` instead of `"ignore"`
2. **Unicode Normalization**: Ensures characters like **ů** display consistently (NFC normalization)  
3. **Strict Detection**: Bad encoding candidates fail early with `char_decode_errors="strict"`
4. **Comprehensive Logging**: Clear visibility into encoding decisions

## Example Results

- **✅ Correct**: `Adamovicím`, `Albrechticích`, `Břeclav`
- **❌ Mojibake**: `AdamovicĄm`, `AlbrechticĄch`, `BreclavĄm`

The tool automatically processes all 30 DBF files in the archive, handling over 19,000 names and 8,600 cities with proper Czech diacritics.