"""Halegannada (Old Kannada) Sandhi Rules and Compound Segmenter."""
import re
from typing import List, Tuple

ADESHA_MAP = {
    "ಕ": "ಗ",
    "ತ": "ದ",
    "ಪ": "ಬ",
}
REVERSE_ADESHA_MAP = {v: k for k, v in ADESHA_MAP.items()}


class HalegannadaSandhiResolver:
    """Applies historical Kannada morphophonemic Sandhi transformations."""

    def generate_surface_variants(self, text: str) -> List[str]:
        """Generate common morphological and Sandhi surface variants for alignment.

        Examples:
        - Adesha Sandhi: ಪ -> ಬ (e.g. ಪೊಣರ್ + ಚಿದ -> ಬೊಣರ್ಚಿದ / ಪೊಣರ್ಚಿದ)
        - Halegannada RRA (ಱ) and RA (ರ) alternation in later copyist manuscripts
        - Halegannada LLA (ೞ) and LA (ಳ/ಲ) sound shifts (ೞ -> ಳ -> ಲ)
        """
        variants = {text}

        # 1. Sound shift: Archaic ೞ (LLA) <-> ಳ (LLA modern)
        if "ೞ" in text:
            variants.add(text.replace("ೞ", "ಳ"))
            variants.add(text.replace("ೞ", "ಲ"))
        if "ಳ" in text:
            variants.add(text.replace("ಳ", "ೞ"))

        # 2. Sound shift: Archaic ಱ (RRA) <-> ರ (RA)
        if "ಱ" in text:
            variants.add(text.replace("ಱ", "ರ"))
        if "ರ" in text:
            variants.add(text.replace("ರ", "ಱ"))

        # 3. Adesha Sandhi substitutions
        for orig, sub in ADESHA_MAP.items():
            if sub in text:
                variants.add(text.replace(sub, orig))

        return list(variants)

    def are_sandhi_equivalent(self, token_a: str, token_b: str) -> bool:
        """Check if two tokens are phonetically identical under Halegannada Sandhi or sound shift."""
        if token_a == token_b:
            return True
        variants_a = set(self.generate_surface_variants(token_a))
        return token_b in variants_a


sandhi_resolver = HalegannadaSandhiResolver()
