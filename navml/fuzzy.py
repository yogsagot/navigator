"""A fuzzy match: whether a few typed letters spell out a longer text, and how well.

``mkd`` finds *Make directory*: the letters are looked for in order, each
anywhere after the last, case ignored.  What makes one text a better answer
than another is where its letters fell -- at the start of a word, one right
after the other, or at the very start of the text -- and how much was skipped
between them, so *Make directory* ranks above *Compare directories* for
``md`` though both hold an ``m`` before a ``d``.

The best placement is found, not the first: ``dir`` in *Directory sizes*
counts the ``d`` that starts the text, not one later.  The texts this is for
are captions -- tens of characters, a few hundred of them -- so the dynamic
programme over query by text is cheap enough to run on every key.

Not :mod:`navml.quick_search`, whose prefix rule is DOS Navigator's own for a
panel's and a tree's Ctrl+S and stays as it is; this is for the command
palette (a departure, asked for) and whatever else searches by letters
rather than by prefix.
"""

from __future__ import annotations

#: What a matched letter is worth by itself.
MATCH = 16
#: More for a letter starting a word, or the text.
WORD_START = 24
#: More for a letter right after the previous matched one.
CONSECUTIVE = 20
#: More again when the whole query is a prefix of the text.
PREFIX = 40
#: Less for each character skipped between two matched letters (capped).
GAP = 2
GAP_CAP = 12
#: Less for each character skipped before the first matched letter (capped).
LEAD = 1
LEAD_CAP = 10

#: What a word starts after.
_SEPARATORS = frozenset(" \t-_/.>:,()[]&+")


def _word_starts(text: str) -> list[bool]:
    starts = []
    previous = ""
    for index, char in enumerate(text):
        starts.append(
            index == 0
            or previous in _SEPARATORS
            or (previous.islower() and char.isupper())
        )
        previous = char
    return starts


def _best(query: str, text: str) -> tuple[int, list[int]] | None:
    """The best score for *query* in *text* and where its letters fell."""
    needle, haystack = query.casefold(), text.casefold()
    # casefold can change a string's length (ß -> ss); match on a text whose
    # indices are the original's where it does not, and give up the
    # placement detail where it does.
    if len(haystack) != len(text):
        haystack = text.lower()
    n, m = len(needle), len(haystack)
    if n == 0:
        return 0, []
    if n > m:
        return None
    starts = _word_starts(text)
    NONE = None
    # best[i][j]: the best score with needle[:i+1] matched and needle[i] at
    # haystack[j]; back[i][j] the j of needle[i-1] that gave it.
    best: list[list[int | None]] = [[NONE] * m for _ in range(n)]
    back: list[list[int]] = [[-1] * m for _ in range(n)]
    for j in range(m):
        if haystack[j] == needle[0]:
            bonus = MATCH + (WORD_START if starts[j] else 0)
            best[0][j] = bonus - min(j * LEAD, LEAD_CAP)
    # A gap of g skipped characters costs min(g * GAP, GAP_CAP): the nearest
    # ``near`` predecessors are weighed one by one, every one further away
    # costs the cap, so the best of those is a running maximum.
    near = GAP_CAP // GAP
    for i in range(1, n):
        row, previous = best[i], best[i - 1]
        far: int | None = NONE  # the best previous[k] with k <= j - 2 - near
        far_at = -1
        for j in range(i, m):
            edge = j - 2 - near
            if edge >= 0 and previous[edge] is not None and (far is None or previous[edge] > far):
                far, far_at = previous[edge], edge
            if haystack[j] != needle[i]:
                continue
            options: list[tuple[int, int]] = []
            if previous[j - 1] is not None:
                options.append((previous[j - 1] + CONSECUTIVE, j - 1))
            for k in range(max(0, j - 1 - near), j - 1):
                if previous[k] is not None:
                    options.append((previous[k] - (j - k - 1) * GAP, k))
            if far is not None:
                options.append((far - GAP_CAP, far_at))
            if not options:
                continue
            value, origin = max(options)
            row[j] = value + MATCH + (WORD_START if starts[j] else 0)
            back[i][j] = origin
    last = best[n - 1]
    end = max((j for j in range(m) if last[j] is not None), key=lambda j: last[j], default=None)
    if end is None:
        return None
    score = last[end]
    assert score is not None
    places = [end]
    for i in range(n - 1, 0, -1):
        places.append(back[i][places[-1]])
    places.reverse()
    if haystack.startswith(needle):
        score += PREFIX
    return score, places


def score(query: str, text: str) -> int | None:
    """How well *query*'s letters spell out *text*, higher better; None when
    they are not all in it in order.  An empty query is 0: everything matches."""
    found = _best(query, text)
    return None if found is None else found[0]


def spans(query: str, text: str) -> list[int]:
    """The indices in *text* of *query*'s letters, as :func:`score` placed
    them; empty when it does not match."""
    found = _best(query, text)
    return [] if found is None else found[1]
