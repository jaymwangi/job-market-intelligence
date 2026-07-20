"""Skill extraction - uses configuration for keywords."""

import re
import json
from typing import List, Set, Optional
from pathlib import Path
from app.etl.enrichment.data.skills import TECH_KEYWORDS


class SkillExtractor:
    """Extract technical skills from job titles and descriptions."""

    def __init__(self, keywords: Optional[List[str]] = None, data_path: Optional[str] = None):
        """
        Initialize skill extractor.

        Args:
            keywords: Technology keywords (if None, uses TECH_KEYWORDS from data)
            data_path: Optional path to external skills data (JSON)
        """
        if keywords is None:
            keywords = TECH_KEYWORDS
        
        self.keywords = self._load_keywords(keywords, data_path)
        self.patterns = self._build_patterns()

    def _load_keywords(self, keywords: List[str], data_path: Optional[str]) -> Set[str]:
        """Load keywords from settings or external file."""
        if data_path:
            try:
                path = Path(data_path)
                if path.exists():
                    with open(path, "r") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            return set(data)
                        if isinstance(data, dict) and "skills" in data:
                            return set(data["skills"])
            except (FileNotFoundError, json.JSONDecodeError):
                # Fall back to keywords from settings
                pass

        return set(k.lower() for k in keywords)

    def _build_patterns(self) -> dict:
        """Build regex patterns for skill extraction."""
        patterns = {}
        for skill in self.keywords:
            # Match skill as whole word, case insensitive
            escaped = re.escape(skill)
            patterns[skill] = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
        return patterns

    def extract_skills(self, title: str, description: str = "") -> List[str]:
        """Extract technical skills from job title and description."""
        text = f"{title} {description}".lower()
        found_skills: Set[str] = set()

        for skill, pattern in self.patterns.items():
            if pattern.search(text):
                found_skills.add(skill)

        return sorted(list(found_skills))

    def extract_from_title(self, title: str) -> List[str]:
        """Extract skills from job title only."""
        return self.extract_skills(title, "")