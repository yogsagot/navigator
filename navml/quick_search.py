"""What a quick search matches: the one rule a file panel and a tree share.

Midnight Commander's: what has been typed is the start of a name, case
folded, with ``*`` and ``?`` as wildcards and everything else literal.
"""

from __future__ import annotations

import re


def name_pattern(text: str) -> re.Pattern[str]:
    """A pattern whose ``match`` says whether a name begins with *text*."""
    return re.compile(
        "".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in text),
        re.IGNORECASE | re.DOTALL,
    )
