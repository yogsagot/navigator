"""The help topics of widgets that cannot name their own.

A dialog or a window names its page with ``help_topic`` in its markup
(``navigator-help`` skill).  navml's own boxes cannot: the library knows no
Navigator page.  So the application gives theirs here, by class name -- the
class's own or any it derives from, the nearest first, so a box derived from
one of these can still name another.

``Navigator.help_topic`` asks :func:`library_topic` of each widget on the way
out from the keyboard that names none itself.  ``tests/test_help_docs.py``
checks every topic here is a page and a heading.
"""

from __future__ import annotations

#: Class name -> topic.
LIBRARY: dict[str, str] = {
    "WindowManagerDialog": "windows.md#window-list",
    "FileDialog": "dialogs.md#choosing-a-file",
}


def library_topic(widget: object) -> str:
    """The topic given to *widget*'s class here, or ""."""
    for cls in type(widget).__mro__:
        topic = LIBRARY.get(cls.__name__)
        if topic:
            return topic
    return ""
