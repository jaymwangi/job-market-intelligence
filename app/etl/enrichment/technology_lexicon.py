"""
Single source of truth for technology term matching.
"""

import re
from typing import Dict, List, Optional, Set, NamedTuple
from app.etl.enrichment.classification_config import ClassificationConfig


class TechnologyMatch(NamedTuple):
    """A matched technology with metadata."""
    term: str           # The matched text
    canonical: str      # Canonical name after alias resolution
    category: str       # Primary category
    start: int          # Start position in text
    end: int            # End position in text


class TechnologyLexicon:
    """Technology vocabulary and matching using shared configuration."""
    
    def __init__(self, config: ClassificationConfig):
        self.config = config
        
        # Build term -> category mapping
        self.term_to_category: Dict[str, str] = {}
        self._build_lexicon()
        
        # Build alias map (alias -> canonical)
        self.alias_to_canonical: Dict[str, str] = {}
        self._build_alias_map()
        
        # Compile efficient regex
        self._compiled_regex = self._compile_regex()
    
    def _build_lexicon(self):
        """Build lexicon from configuration."""
        for cat_id, cat_config in self.config.categories.items():
            for keyword in cat_config.keywords.keys():
                self.term_to_category[keyword.lower()] = cat_id
    
    def _build_alias_map(self):
        """Build alias map for normalized matching."""
        self.alias_to_canonical = {
            k.lower(): v.lower()
            for k, v in self.config.aliases.items()
        }
        
        # Also ensure canonical terms are in the alias map
        for term in self.term_to_category.keys():
            if term not in self.alias_to_canonical:
                self.alias_to_canonical[term] = term
    
    def _compile_regex(self) -> re.Pattern:
        """Compile a single efficient regex for all terms."""
        # Include all terms and aliases
        terms = list(self.term_to_category.keys())
        terms.extend(self.alias_to_canonical.keys())
        
        # Remove duplicates
        terms = list(set(terms))
        
        # Sort by length descending for proper matching
        terms.sort(key=len, reverse=True)
        
        # Escape for regex
        escaped = [re.escape(term) for term in terms]
        
        # Build pattern with word boundaries
        pattern = r'\b(' + '|'.join(escaped) + r')\b'
        
        return re.compile(pattern, re.IGNORECASE)
    
    def find_technologies(self, text: str) -> List[TechnologyMatch]:
        """Find all technology mentions in text with metadata."""
        matches = []
        seen = set()  # Track seen canonical terms to avoid duplicates
        
        for match in self._compiled_regex.finditer(text):
            term = match.group(0).lower()
            
            # Resolve alias
            canonical = self.alias_to_canonical.get(term, term)
            
            # Skip if we've already found this canonical term
            if canonical in seen:
                continue
            seen.add(canonical)
            
            # Get category
            category = self.term_to_category.get(canonical, 'unknown')
            
            matches.append(TechnologyMatch(
                term=term,
                canonical=canonical,
                category=category,
                start=match.start(),
                end=match.end(),
            ))
        
        return matches
    
    def get_canonical_terms(self) -> List[str]:
        """Get all canonical technology terms."""
        return list(self.term_to_category.keys())
    
    def get_aliases(self) -> Dict[str, str]:
        """Get alias mapping."""
        return self.alias_to_canonical.copy()
    
    def stats(self) -> Dict[str, int]:
        """Get statistics about the lexicon."""
        return {
            'canonical_terms': len(self.term_to_category),
            'aliases': len(self.alias_to_canonical),
            'categories': len(set(self.term_to_category.values())),
        }


# ============================================================
# Singleton
# ============================================================

_lexicon: Optional[TechnologyLexicon] = None


def get_lexicon() -> TechnologyLexicon:
    """Get the singleton TechnologyLexicon instance."""
    global _lexicon
    
    if _lexicon is None:
        from app.etl.enrichment.classification_config import get_config
        _lexicon = TechnologyLexicon(get_config())
    
    return _lexicon


# ============================================================
# Export
# ============================================================

__all__ = [
    'TechnologyMatch',
    'TechnologyLexicon',
    'get_lexicon',
]
