"""What the progress box's one button means; the gauge is a ``ProgressBar``."""

from __future__ import annotations

from typing import Any

from navkit.reactive import unbind

from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog


class SearchProgress(Dialog):
    """*Search Progress*: a gauge, a percentage, and *Stop*.

    The gauge is ``bar``, a :class:`~navml.widgets.progress_bar.ProgressBar`,
    and the percentage is what it says.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # DN's ``dlStop``: the dialog's own button, renamed.  Unbound first,
        # because `Dialog' binds the OK caption to its `buttons' (*Yes* for
        # yes-no-cancel) and a value cannot be assigned over a binding.
        unbind(self.ok, Button.text)
        self.ok.text = "~S~top"

    def accept(self) -> Any:
        """*Stop* answers what Esc does: nothing, which is a stopped search."""
        return None
