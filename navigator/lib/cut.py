"""DN's ``Cut``: a path shortened in its middle to a width."""

from __future__ import annotations


def cut_path(text: str, width: int = 30) -> str:
    """DN's ``Cut(S, Len)`` (``ADVANCE.PAS:901``): *text* whole if it fits, else its
    first two characters, ``...`` and its end -- ``Len - 1`` characters in all,
    as ``Delete(p, 3, L - Len + 4); Insert('...', p, 3)`` left it."""
    if len(text) <= width:
        return text
    return text[:2] + "..." + text[len(text) - (width - 6):]
