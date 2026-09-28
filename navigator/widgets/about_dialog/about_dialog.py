"""What markup cannot say about the About box: how its text is drawn.

The text is ``Dialog``'s own ``message``, a child of the base, and a derived
document has no line that reaches a base's child -- so the centring, which was
the ``^C`` on every line of DOS Navigator's ``dlAbout``, is said here, and so
is making the home page a link the terminal can open.
"""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog


class AboutDialog(Dialog):
    """≡ > About: the name, the version, the licence and the author."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.message.align = "center"
        self.message.links = True
