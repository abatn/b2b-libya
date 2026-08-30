"""
Libya B2B Platform - Search Service
Fuzzy full-text search with scoring.
"""


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)
    len1, len2 = len(s1), len(s2)
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j - 1] + cost,
            )
    return matrix[len1][len2]


def similarity_ratio(s1: str, s2: str) -> float:
    """Similarity ratio between 0 and 1."""
    if not s1 or not s2:
        return 0.0
    if s1.lower() == s2.lower():
        return 1.0
    dist = levenshtein_distance(s1.lower(), s2.lower())
    max_len = max(len(s1), len(s2))
    return 1.0 - (dist / max_len) if max_len > 0 else 0.0


def fuzzy_score(query: str, text: str) -> float:
    """Score how well query matches text. Returns 0-1."""
    if not text or not query:
        return 0.0
    q = query.lower()
    t = text.lower()
    if q == t:
        return 1.0
    if t.startswith(q):
        return 0.95
    if q in t:
        return 0.85
    # Word-level
    q_words = q.split()
    t_words = t.split()
    word_hits = sum(1 for w in q_words if any(w in tw for tw in t_words))
    if word_hits > 0:
        return 0.7 + 0.15 * (word_hits / len(q_words))
    # Fuzzy per word
    best = 0.0
    for qw in q_words:
        for tw in t_words:
            ratio = similarity_ratio(qw, tw)
            if ratio > best:
                best = ratio
    return best * 0.6
