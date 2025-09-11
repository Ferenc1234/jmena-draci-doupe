#!/usr/bin/env python3
"""
Test the diacritizer with CSV data to demonstrate PAD2 preference.
"""

import pandas as pd
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from diacritizer import CzechDiacritizer


def test_csv_diacritization():
    """Test diacritization on CSV data."""
    print("Testing CSV Diacritization")
    print("=" * 40)
    
    # Create test data
    test_data = {
        'JMENO': ['Pavel', 'Tomas', 'Petr'],
        'PAD1': ['Pavel', 'Tomas', 'Petr'],  # Nominative (unchanged)
        'PAD2': ['Pavla', 'Tomase', 'Petra'],  # Genitive (some should change to -ů)
        'PAD3': ['Pavlovi', 'Tomasovi', 'Petrovi']  # Dative
    }
    
    df = pd.DataFrame(test_data)
    print("Original data:")
    print(df)
    print()
    
    # Initialize diacritizer
    diacritizer = CzechDiacritizer(prefer_genpl_uu=True)
    
    # Process each PAD column
    for col in df.columns:
        if col.startswith('PAD'):
            print(f"Processing column {col}:")
            original_values = df[col].tolist()
            diacritized_values = diacritizer.diacritize_column(original_values, col)
            
            print(f"  Original:    {original_values}")
            print(f"  Diacritized: {diacritized_values}")
            
            # Show changes
            changes = [(orig, new) for orig, new in zip(original_values, diacritized_values) if orig != new]
            if changes:
                print(f"  Changes: {changes}")
            else:
                print("  No changes made")
            print()
            
            # Update DataFrame
            df[col] = diacritized_values
    
    print("Final data:")
    print(df)
    print()
    
    # Print statistics
    diacritizer.print_stats()


def main():
    """Run the CSV diacritizer test."""
    try:
        test_csv_diacritization()
        print("\n✓ Test completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()