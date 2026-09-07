import re
from dataclasses import dataclass, field
from re import Pattern


@dataclass(frozen=True)
class TitlePattern:
    """A title pattern with category mapping, weight, and strength."""

    pattern: str
    categories: tuple[str, ...] = field(default_factory=tuple)
    weight: float = 8.0
    strength: str = "potential"  # strong, potential, adjacent, ambiguous
    specificity: str = "medium"  # high, medium, low
    compiled: Pattern[str] | None = field(default=None, compare=False, hash=False)

    def __post_init__(self) -> None:
        """Compile the regex pattern."""
        # Ensure pattern is a string
        if not isinstance(self.pattern, str):
            raise ValueError(f"Pattern must be a string, got {type(self.pattern)}")

        # Convert categories to tuple if needed
        if isinstance(self.categories, list):  # type: ignore[unreachable]  # type: ignore[unreachable]
            object.__setattr__(self, "categories", tuple(self.categories))  # type: ignore[unreachable]  # type: ignore[unreachable]

        # Compile the pattern if not already compiled
        if self.compiled is None:
            try:
                object.__setattr__(self, "compiled", re.compile(self.pattern, re.IGNORECASE))
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{self.pattern}': {e}")

    def matches(self, title: str) -> bool:
        """Check if the title matches this pattern."""
        if not title or self.compiled is None:
            return False
        return bool(self.compiled.search(title))

    @property
    def is_strong(self) -> bool:
        return self.strength == "strong"

    @property
    def is_potential(self) -> bool:
        return self.strength == "potential"

    @property
    def is_adjacent(self) -> bool:
        return self.strength == "adjacent"

    @property
    def is_ambiguous(self) -> bool:
        return self.strength == "ambiguous"

    @property
    def strength_priority(self) -> int:
        """Get priority level for strength comparison (higher = stronger)."""
        priorities = {
            "strong": 4,
            "potential": 3,
            "adjacent": 2,
            "ambiguous": 1,
        }
        return priorities.get(self.strength, 0)
