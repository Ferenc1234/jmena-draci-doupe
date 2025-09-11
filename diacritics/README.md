# Czech Diacritics Restoration Module

This module automatically restores Czech diacritics in text that was stored without proper diacritical marks.

## Files

- `restore_diacritics.py` - Main diacritics restoration engine
- `overrides.tsv` - Manual overrides for specific words (tab-separated format)
- `__init__.py` - Module initialization

## How It Works

1. **Text Tokenization**: Splits text into words and non-word segments (preserving punctuation/whitespace)

2. **Diacritics Stripping**: Removes diacritics from words using Unicode normalization to create mapping keys

3. **Dictionary Lookup**: Uses two sources for restoration:
   - **Manual Overrides** (highest priority): Custom corrections from `overrides.tsv`
   - **MorfFlex Dictionary**: Czech morphological dictionary forms

4. **Case Preservation**: Maintains original capitalization patterns (UPPER, Title, lower)

5. **Safe Processing**: Returns original text if no match found, preserves non-Czech text

## Manual Overrides Format

The `overrides.tsv` file uses tab-separated format:

```
stripped	diacritized	comment
bazina	bažina	marsh/swamp
krkavcu	krkavců	ravens (genitive plural)
mrtvych	mrtvých	dead (genitive plural)
```

- **stripped**: Word without diacritics (case insensitive)
- **diacritized**: Correct form with diacritics  
- **comment**: Optional description/notes

## Usage

### Standalone

```python
from diacritics import DiacriticsRestorer

restorer = DiacriticsRestorer()
result = restorer.restore_text_diacritics("Bazina mrtvych krkavcu")
print(result)  # "Bažina mrtvých krkavců"
```

### In convert_drd_names.py

Diacritics restoration is enabled by default:

```bash
# With diacritics restoration (default)
python convert_drd_names.py "jmena(1).zip"

# Disable diacritics restoration
python convert_drd_names.py "jmena(1).zip" --no-diacritics
```

## Dictionary Source

The module is designed to use MorfFlex CZ (Czech morphological dictionary) from UFAL. For this implementation, it includes a simplified Czech word list with common forms. In production, you would:

1. Download MorfFlex CZ from UFAL (https://lindat.mff.cuni.cz/)
2. Extract word forms
3. Build stripped-form → diacritized-forms mapping

## Performance

- Dictionary loads once per session and is reused across multiple files
- Manual overrides take priority over dictionary lookups
- Preserves original text structure and formatting
- Handles large datasets efficiently (tested with 19,000+ records)

## Limitations

- Currently uses simplified dictionary (production would need full MorfFlex)
- Context-insensitive (chooses first dictionary match)
- Designed specifically for Czech language
- May not handle all edge cases or archaic forms