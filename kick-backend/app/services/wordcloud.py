"""Word frequency analysis for chat word cloud overlay."""

import re
from collections import Counter

STOP_WORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her",
    "she", "or", "an", "will", "my", "one", "all", "would", "there",
    "their", "what", "so", "up", "out", "if", "about", "who", "get",
    "which", "go", "me", "when", "make", "can", "like", "time", "no",
    "just", "him", "know", "take", "people", "into", "year", "your",
    "some", "could", "them", "see", "other", "than", "then", "now",
    "look", "only", "come", "its", "over", "also", "back", "after",
    "use", "two", "how", "our", "way", "even", "because", "any",
    "these", "give", "most", "us", "is", "are", "was", "were", "been",
    "has", "had", "did", "does", "am", "im", "dont", "cant", "wont",
    "isnt", "arent", "wasnt", "werent", "shouldnt", "wouldnt", "couldnt",
    "thats", "its", "lets", "hes", "shes", "theyre", "youre", "were",
}

URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
COMMAND_PATTERN = re.compile(r"^![a-zA-Z]")
EMOTE_PATTERN = re.compile(r":[a-zA-Z0-9_]+:")


def extract_word_frequencies(
    messages: list[str],
    max_words: int = 100,
    excluded_words: list[str] | None = None,
) -> list[dict]:
    """Analyze messages and return word frequencies."""
    extra_excluded = {w.lower() for w in (excluded_words or [])}
    word_counter: Counter[str] = Counter()

    for msg in messages:
        # Skip bot commands
        if COMMAND_PATTERN.match(msg):
            continue
        # Remove URLs
        text = URL_PATTERN.sub("", msg)
        # Remove emote codes
        text = EMOTE_PATTERN.sub("", text)
        # Tokenize
        words = re.findall(r"[a-zA-Z]{2,}", text.lower())
        for word in words:
            if word not in STOP_WORDS and word not in extra_excluded and len(word) <= 30:
                word_counter[word] += 1

    top_words = word_counter.most_common(max_words)
    if not top_words:
        return []

    max_count = top_words[0][1]
    return [
        {"word": word, "count": count, "weight": round(count / max_count, 3)}
        for word, count in top_words
    ]
