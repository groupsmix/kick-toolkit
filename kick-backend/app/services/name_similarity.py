"""Enhanced username pattern matching with edit-distance and leetspeak detection."""

import re
from difflib import SequenceMatcher


# Leetspeak substitution map
_LEET_MAP: dict[str, str] = {
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "8": "b", "9": "g", "@": "a", "$": "s",
    "!": "i", "|": "l", "(": "c", "+": "t",
}

# Common prefix/suffix patterns to strip
_STRIP_PATTERNS = re.compile(
    r"^(xx_?|x_|_)|(_?xx|_x|_alt\d*|_new\d*|_temp\d*|\d+)$",
    re.IGNORECASE,
)

# Suspicious substrings
_SUS_PATTERNS = [
    "xx", "alt", "new", "temp", "fake", "bot", "spam", "test",
    "throw", "smurf", "anon", "burner",
]


def _normalize_leet(name: str) -> str:
    """Convert leetspeak characters to their alphabetic equivalents."""
    return "".join(_LEET_MAP.get(c, c) for c in name.lower())


def _strip_decorations(name: str) -> str:
    """Remove common prefix/suffix decorations and trailing digits."""
    cleaned = _STRIP_PATTERNS.sub("", name.lower())
    # Strip leading/trailing underscores left behind
    cleaned = cleaned.strip("_")
    return cleaned if cleaned else name.lower()


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def compute_similarity(name1: str, name2: str) -> float:
    """Compute similarity score between two usernames (0.0 - 1.0).

    Uses multiple techniques:
    1. Direct SequenceMatcher ratio
    2. Levenshtein-based similarity
    3. Leetspeak-normalized comparison
    4. Decoration-stripped comparison
    """
    n1 = name1.lower()
    n2 = name2.lower()

    if n1 == n2:
        return 1.0

    scores: list[float] = []

    # 1. Direct sequence matching
    scores.append(SequenceMatcher(None, n1, n2).ratio())

    # 2. Levenshtein similarity
    max_len = max(len(n1), len(n2))
    if max_len > 0:
        lev_dist = _levenshtein_distance(n1, n2)
        scores.append(1.0 - (lev_dist / max_len))

    # 3. Leetspeak-normalized
    leet1 = _normalize_leet(n1)
    leet2 = _normalize_leet(n2)
    if leet1 != n1 or leet2 != n2:
        scores.append(SequenceMatcher(None, leet1, leet2).ratio())

    # 4. Decoration-stripped
    stripped1 = _strip_decorations(n1)
    stripped2 = _strip_decorations(n2)
    if stripped1 != n1 or stripped2 != n2:
        scores.append(SequenceMatcher(None, stripped1, stripped2).ratio())

    return max(scores)


def find_similar_names(
    username: str,
    banned_names: list[str],
    threshold: float = 0.65,
) -> list[tuple[str, float]]:
    """Find banned names similar to the given username.

    Returns list of (banned_name, similarity_score) above threshold,
    sorted by similarity descending.
    """
    results: list[tuple[str, float]] = []
    for banned in banned_names:
        score = compute_similarity(username, banned)
        if score >= threshold:
            results.append((banned, score))
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def has_suspicious_pattern(username: str) -> bool:
    """Check if username contains suspicious substrings."""
    lower = username.lower()
    return any(p in lower for p in _SUS_PATTERNS)


def get_pattern_flags(username: str) -> list[str]:
    """Return list of pattern-based flags for a username."""
    flags: list[str] = []
    lower = username.lower()
    for p in _SUS_PATTERNS:
        if p in lower:
            flags.append(f"Username contains '{p}'")
            break  # Only report first match
    return flags
