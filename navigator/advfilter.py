"""Alt+Del's *Filter*: DOS Navigator's ``CM_AdvancedFilter`` (FLTOOLS.PAS).

The box lists ``*`` and a ``*.ext`` for every extension a file in the
directory has -- those the panel's mask hides too, as DN read the directory
again with ``*.*`` -- and *Show* or *Hide* folds what is marked into the
panel's file mask (``Panel.file_mask``, read by
:func:`navigator.filetypes.in_filter`, the last pattern that matches
deciding).

DN joined the masks with string surgery that wrote ``- *.X`` in one place
and ``-*.X`` in another; the intent is kept, the surgery not: *Show* ``*``
or *Hide* ``*`` sets the whole mask; from a mask that shows everything, *Show*
makes one that shows the chosen alone and *Hide* one that shows the rest;
otherwise a chosen pattern takes the place of whatever the mask said of it,
at the end, where it decides.  A name without an extension has no ``*.ext``
here, as it had none in DN's box.
"""

from __future__ import annotations

from typing import Any, Iterable

from navigator.filetypes import ALL_FILES, patterns


def extensions(entries: Iterable[Any]) -> list[str]:
    """The box's masks: ``*`` first, then each file's ``*.ext`` once, sorted."""
    found: set[str] = set()
    for entry in entries:
        if entry.is_dir or entry.name == "..":
            continue
        stem, dot, extension = entry.name.rpartition(".")
        if dot and stem and extension:
            found.add(f"*.{extension}")
    return [ALL_FILES, *sorted(found, key=lambda mask: (mask.lower(), mask))]


def combine(mask: str, chosen: Iterable[str], show: bool) -> str:
    """*mask* with *chosen* shown, or hidden."""
    chosen = list(dict.fromkeys(chosen))
    if not chosen:
        return mask
    if ALL_FILES in chosen:
        return ALL_FILES if show else f"-{ALL_FILES}"
    current = patterns(mask.replace(" ", "")) or [ALL_FILES]
    if current == [ALL_FILES]:
        if show:
            return ";".join(chosen)
        return ";".join([ALL_FILES, *(f"-{each}" for each in chosen)])
    kept = [each for each in current if each.lstrip("-") not in chosen]
    added = chosen if show else [f"-{each}" for each in chosen]
    return ";".join(kept + added)
