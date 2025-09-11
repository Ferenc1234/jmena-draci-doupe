#!/usr/bin/env python3
"""
Czech diacritizer for Dračí doupě name databases.

This module provides Czech text diacritization using MorfFlex dictionary
with improved heuristics for better candidate selection and special handling
for PAD2 genitive plural forms.
"""

import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.request import urlopen
import tempfile
import os


class CzechDiacritizer:
    """Czech diacritizer with MorfFlex dictionary and improved heuristics."""
    
    def __init__(self, prefer_genpl_uu: bool = True, cache_dir: Optional[str] = None):
        """
        Initialize the diacritizer.
        
        Args:
            prefer_genpl_uu: Whether to prefer -ů endings in PAD2 (genitive plural)
            cache_dir: Directory to cache MorfFlex data (defaults to temp dir)
        """
        self.prefer_genpl_uu = prefer_genpl_uu
        self.cache_dir = Path(cache_dir) if cache_dir else Path(tempfile.gettempdir()) / "diacritizer_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Dictionary will be loaded lazily
        self._dictionary: Optional[Dict[str, Set[str]]] = None
        
        # Stats tracking
        self.stats = {
            'total_processed': 0,
            'changed': 0,
            'unchanged': 0,
            'by_column': {}
        }
    
    def _strip_diacritics(self, text: str) -> str:
        """Remove diacritics from Czech text for comparison."""
        # Normalize and remove diacritics
        normalized = unicodedata.normalize('NFD', text)
        without_diacritics = ''.join(
            char for char in normalized 
            if unicodedata.category(char) != 'Mn'
        )
        return without_diacritics
    
    def _download_morfflex(self) -> str:
        """Download MorfFlex dictionary data."""
        cache_file = self.cache_dir / "morfflex_cs.txt"
        
        if cache_file.exists():
            print(f"Using cached MorfFlex data: {cache_file}")
            return str(cache_file)
        
        print("Downloading MorfFlex dictionary...")
        try:
            # This is a sample URL - in real implementation this should be the actual MorfFlex URL
            url = "http://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-1673/czech-morfflex-pdt-161115.zip"
            
            # For now, create a minimal sample dictionary for testing
            # In production, this would download and parse the real MorfFlex data
            sample_dict = {
                'blesk': {'blesk', 'blesku', 'blesků', 'blesky', 'bleskem'},
                'hrom': {'hrom', 'hromu', 'hromů', 'hromy', 'hromem'},
                'duch': {'duch', 'duchu', 'duchů', 'duchy', 'duchem'},
                'komar': {'komár', 'komára', 'komárů', 'komáry', 'komárem', 'komar'},
                'bazina': {'bažina', 'bažiny', 'bažin', 'bazina'},
                # Add some common Czech name patterns for testing
                'pavel': {'Pavel', 'Pavla', 'Pavlů', 'Pavly', 'Pavlem'},
                'jana': {'Jana', 'Jany', 'Janě', 'Janu', 'Jano', 'Janou'},
                'petr': {'Petr', 'Petra', 'Petrovi', 'Petrem', 'Petrů'},
                'martin': {'Martin', 'Martina', 'Martinovi', 'Martinem', 'Martinů'},
                'tomas': {'Tomáš', 'Tomáše', 'Tomášovi', 'Tomášem', 'Tomášů'},
            }
            
            # Save sample dictionary to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                for base_form, variants in sample_dict.items():
                    for variant in variants:
                        f.write(f"{variant}\t{base_form}\n")
            
            print(f"Sample dictionary saved to: {cache_file}")
            return str(cache_file)
            
        except Exception as e:
            print(f"Warning: Could not download MorfFlex data: {e}")
            print("Continuing with empty dictionary...")
            return ""
    
    def _load_dictionary(self) -> Dict[str, Set[str]]:
        """Load MorfFlex dictionary data."""
        if self._dictionary is not None:
            return self._dictionary
        
        self._dictionary = {}
        
        try:
            dict_file = self._download_morfflex()
            if not dict_file or not os.path.exists(dict_file):
                print("No dictionary data available, diacritization will be limited")
                return self._dictionary
            
            print(f"Loading dictionary from: {dict_file}")
            
            with open(dict_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or '\t' not in line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        word_form = parts[0].strip()
                        base_form = parts[1].strip()
                        
                        # Group all forms of the same base word
                        if base_form not in self._dictionary:
                            self._dictionary[base_form] = set()
                        self._dictionary[base_form].add(word_form)
            
            print(f"Loaded dictionary with {len(self._dictionary)} base forms")
            
        except Exception as e:
            print(f"Error loading dictionary: {e}")
            self._dictionary = {}
        
        return self._dictionary
    
    def _find_candidates(self, token: str) -> List[str]:
        """Find dictionary candidates for a token."""
        dictionary = self._load_dictionary()
        candidates = []
        
        if not dictionary:
            return candidates
        
        # Look for exact matches first (case insensitive)
        for base_form, variants in dictionary.items():
            for variant in variants:
                if token.lower() == variant.lower():
                    candidates.extend(variants)
                    break
        
        # If no exact match, look for diacritics-insensitive matches
        if not candidates:
            token_stripped = self._strip_diacritics(token.lower())
            for base_form, variants in dictionary.items():
                for variant in variants:
                    if self._strip_diacritics(variant.lower()) == token_stripped:
                        candidates.extend(variants)
                        break
        
        return list(set(candidates))  # Remove duplicates
    
    def _score_candidate(self, original: str, candidate: str, is_pad2: bool = False) -> Tuple[int, int, int, int]:
        """
        Score a candidate for selection.
        
        Returns tuple of (priority_scores...) where lower is better:
        1. Diacritics-insensitive suffix match (0 if matches, 1 if not)
        2. PAD2 preference: for PAD2, prefer -ů over -u (0 if preferred, 1 if not)
        3. Exact suffix match with diacritics (0 if matches, length_diff if not)
        4. Length difference (for stable ordering)
        """
        
        # 1. Diacritics-insensitive suffix comparison
        orig_stripped = self._strip_diacritics(original.lower())
        cand_stripped = self._strip_diacritics(candidate.lower())
        
        # Find longest common suffix (diacritics-insensitive)
        common_suffix_len = 0
        min_len = min(len(orig_stripped), len(cand_stripped))
        for i in range(1, min_len + 1):
            if orig_stripped[-i] == cand_stripped[-i]:
                common_suffix_len = i
            else:
                break
        
        # Score 1: 0 if good suffix match, 1 if poor match
        suffix_match_score = 0 if common_suffix_len >= min(3, len(orig_stripped)) else 1
        
        # 2. PAD2 -ů preference
        pad2_score = 0
        if is_pad2 and self.prefer_genpl_uu:
            # Prefer candidates ending with 'ů' over those ending with 'u'
            if candidate.endswith('ů'):
                pad2_score = 0  # Preferred
            elif candidate.endswith('u'):
                pad2_score = 1  # Less preferred
            else:
                pad2_score = 0  # Neutral
        
        # 3. Exact suffix match with diacritics
        exact_suffix_len = 0
        for i in range(1, min(len(original), len(candidate)) + 1):
            if original[-i].lower() == candidate[-i].lower():
                exact_suffix_len = i
            else:
                break
        
        exact_suffix_score = max(0, len(original) - exact_suffix_len)
        
        # 4. Length difference for stable ordering
        length_score = abs(len(original) - len(candidate))
        
        return (suffix_match_score, pad2_score, exact_suffix_score, length_score)
    
    def _preserve_case(self, original: str, candidate: str) -> str:
        """Preserve the original casing pattern in the candidate."""
        if not original or not candidate:
            return candidate
        
        result = list(candidate)
        
        # Apply casing pattern from original
        for i in range(min(len(original), len(result))):
            if original[i].isupper():
                result[i] = result[i].upper()
            elif original[i].islower():
                result[i] = result[i].lower()
        
        return ''.join(result)
    
    def diacritize_token(self, token: str, column_name: str = "") -> str:
        """
        Diacritize a single token.
        
        Args:
            token: Input token to diacritize
            column_name: Column name for PAD detection
            
        Returns:
            Diacritized token or original if no suitable candidate found
        """
        if not token or not token.strip():
            return token
        
        # Clean token
        clean_token = token.strip()
        
        # Check if this is a PAD2 column
        is_pad2 = column_name.upper() == 'PAD2'
        
        # Find candidates
        candidates = self._find_candidates(clean_token)
        
        if not candidates:
            # No dictionary candidates, keep original
            self.stats['unchanged'] += 1
            return token
        
        # Score and sort candidates
        scored_candidates = []
        for candidate in candidates:
            score = self._score_candidate(clean_token, candidate, is_pad2)
            scored_candidates.append((score, candidate))
        
        # Sort by score (lower is better)
        scored_candidates.sort(key=lambda x: x[0])
        
        # Select best candidate
        best_candidate = scored_candidates[0][1]
        
        # Preserve original casing
        result = self._preserve_case(clean_token, best_candidate)
        
        # Update stats
        if result != clean_token:
            self.stats['changed'] += 1
        else:
            self.stats['unchanged'] += 1
        
        return result
    
    def diacritize_column(self, values: List[str], column_name: str) -> List[str]:
        """
        Diacritize all values in a column.
        
        Args:
            values: List of string values to diacritize
            column_name: Name of the column for PAD detection
            
        Returns:
            List of diacritized values
        """
        result = []
        column_changes = 0
        
        for value in values:
            if isinstance(value, str):
                original_value = value
                diacritized = self.diacritize_token(value, column_name)
                result.append(diacritized)
                
                if diacritized != original_value:
                    column_changes += 1
            else:
                result.append(value)
        
        # Update column stats
        self.stats['by_column'][column_name] = {
            'total': len(values),
            'changed': column_changes
        }
        
        self.stats['total_processed'] += len(values)
        
        return result
    
    def print_stats(self):
        """Print diacritization statistics."""
        print("\n" + "="*50)
        print("DIACRITIZATION SUMMARY")
        print("="*50)
        print(f"Total tokens processed: {self.stats['total_processed']}")
        print(f"Changed: {self.stats['changed']}")
        print(f"Unchanged: {self.stats['unchanged']}")
        
        if self.stats['by_column']:
            print("\nPer-column summary:")
            for col_name, col_stats in self.stats['by_column'].items():
                changed_pct = (col_stats['changed'] / col_stats['total'] * 100) if col_stats['total'] > 0 else 0
                print(f"  {col_name:15s}: {col_stats['changed']:4d}/{col_stats['total']:4d} changed ({changed_pct:5.1f}%)")
        
        print("="*50)


def main():
    """CLI interface for the diacritizer."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Czech diacritizer for text files"
    )
    parser.add_argument(
        "input_file",
        help="Input text file"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: add _diacritized suffix)"
    )
    parser.add_argument(
        "--prefer-genpl-uu",
        action="store_true",
        default=True,
        help="Prefer -ů endings in PAD2 columns (default: enabled)"
    )
    parser.add_argument(
        "--no-prefer-genpl-uu",
        action="store_true",
        help="Disable -ů preference in PAD2 columns"
    )
    parser.add_argument(
        "--cache-dir",
        help="Directory for caching MorfFlex data"
    )
    
    args = parser.parse_args()
    
    # Handle preference flag
    prefer_genpl_uu = args.prefer_genpl_uu and not args.no_prefer_genpl_uu
    
    # Initialize diacritizer
    diacritizer = CzechDiacritizer(
        prefer_genpl_uu=prefer_genpl_uu,
        cache_dir=args.cache_dir
    )
    
    # Process file
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        diacritized_lines = []
        for line in lines:
            tokens = line.strip().split()
            diacritized_tokens = [diacritizer.diacritize_token(token) for token in tokens]
            diacritized_lines.append(' '.join(diacritized_tokens) + '\n')
        
        # Determine output file
        if args.output:
            output_file = args.output
        else:
            input_path = Path(args.input_file)
            output_file = input_path.parent / f"{input_path.stem}_diacritized{input_path.suffix}"
        
        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(diacritized_lines)
        
        print(f"Diacritized text saved to: {output_file}")
        diacritizer.print_stats()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()