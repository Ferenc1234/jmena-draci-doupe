"""
Diacritics restoration module for Czech text.

This module provides functionality to restore Czech diacritics in text
that was stored without proper diacritical marks.
"""

from .restore_diacritics import DiacriticsRestorer

__all__ = ['DiacriticsRestorer']