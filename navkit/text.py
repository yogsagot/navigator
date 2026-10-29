"""Turbo Vision's marked text: ``~`` toggling a highlight on and off.

What a caption marks its shortcut letter with, and what a tooltip marks a key
with (:class:`navkit.tooltip.Markup`).  In navkit rather than in navml's
``Control`` because a tooltip is navkit's and navkit depends on nothing
above it; navml re-exports both from ``navml.widgets.dialog.control``.
"""

from __future__ import annotations

from navkit.bidi import reveal


def caption_runs(text: str) -> list[tuple[str, bool]]:
    """*text* as runs of plain and marked characters, in order.

    What Turbo Vision's ``MoveCStr`` drew: every ``~`` toggles the highlight,
    so a caption may mark more than one run -- DOS Navigator's Copy prompt
    marks the file name as well as its letter.  ``~~`` is one literal tilde,
    inside a marked run as well as outside one, which is what lets a file
    name be put in a caption; a ``~`` left over with nothing to pair with is
    drawn as one too -- a caption is text first and a declaration second.
    """
    toggles: list[int] = []
    index = 0
    while index < len(text):
        if text[index] == "~":
            if text[index + 1 : index + 2] == "~":
                index += 2
                continue
            toggles.append(index)
        index += 1
    if len(toggles) % 2:
        toggles.pop()                # unpaired: drawn, not obeyed
    toggle_at = set(toggles)
    runs: list[tuple[str, bool]] = []
    current: list[str] = []
    marked = False
    index = 0
    while index < len(text):
        if index in toggle_at:
            if current:
                runs.append(("".join(current), marked))
                current = []
            marked = not marked
            index += 1
            continue
        if text[index : index + 2] == "~~":
            current.append("~")      # `~~' is one literal tilde
            index += 2
            continue
        current.append(text[index])
        index += 1
    if current:
        runs.append(("".join(current), marked))
    return runs


def escape_caption(text: str) -> str:
    """*text* with every ``~`` doubled, so a file name is drawn as it is --
    and a direction override or a control in it shown as ``⁇``
    (:func:`navkit.bidi.reveal`), so it cannot turn the name round.  Line
    breaks and tabs are a caption's own and stay."""
    return reveal(text, keep="\n\t").replace("~", "~~")
