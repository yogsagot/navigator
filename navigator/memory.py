"""Whether a file fits in memory: DN's ``MemAvail`` check and ``OutOfMemory``.

DN's editor refused a file before reading it if it was larger than the memory
left (``S^.GetSize > MemAvail - $4000``), and again after counting its lines
(``4*(LCount+50)+FFSize``), with ``erNotEnoughMemory``.  A 13 GB file read
into Python lines does not fail politely: the kernel's OOM killer takes the
whole process, or swap takes the machine.  So the editor asks first, here.

What is asked is Linux's ``MemAvailable`` -- what can be allocated without
swapping -- and the system's free pages where there is no ``/proc``.  Nothing
known is no guard: a refusal on a guess would be worse than DN's silence.
"""

from __future__ import annotations

import os
from typing import Any

#: DN's ``erNotEnoughMemory``.
NOT_ENOUGH_MEMORY = "Not enough memory to complete operation."

#: The share of available memory a text may take: the rest is the undo
#: stack's, the rest of Navigator's, and other programs'.  DN's ``$4000``.
EDIT_BUDGET = 0.75


class NotEnoughMemory(MemoryError):
    """The text would not fit.  Not an ``OSError``: no file is at fault."""


def parse_meminfo(text: str) -> int | None:
    """``MemAvailable`` from a ``/proc/meminfo``, in bytes, or None if absent."""
    for line in text.splitlines():
        if line.startswith("MemAvailable:"):
            fields = line.split()
            try:
                value = int(fields[1])
            except (IndexError, ValueError):
                return None
            unit = fields[2].lower() if len(fields) > 2 else "kb"
            return value * 1024 if unit == "kb" else value
    return None


def available_memory() -> int | None:
    """How many bytes can be allocated without swapping, or None if not known."""
    try:
        with open("/proc/meminfo", encoding="ascii", errors="replace") as file:
            found = parse_meminfo(file.read())
        if found is not None:
            return found
    except OSError:
        pass
    try:
        pages = os.sysconf("SC_AVPHYS_PAGES")
        size = os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, ValueError, OSError):
        return None
    if pages <= 0 or size <= 0:
        return None
    return pages * size


def edit_budget() -> int | None:
    """How many bytes a text read into the editor may take, or None for no limit."""
    available = available_memory()
    return None if available is None else int(available * EDIT_BUDGET)


async def out_of_memory(app: Any) -> None:
    """``TApplication.OutOfMemory``: say so, and nothing else happens."""
    from navml.widgets.dialog.dialog import Dialog

    await Dialog(title="Error", prompt=NOT_ENOUGH_MEMORY, buttons="ok").execute(app)
