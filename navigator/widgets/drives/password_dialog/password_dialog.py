"""What OK answers: the password, and whether to keep it."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog


class PasswordDialog(Dialog):
    """A password or a passphrase, never shown and never copied."""

    def __init__(self, prompt: str = "", *, can_keep: bool = False, **kwargs: Any) -> None:
        """*prompt* says what for; *can_keep* offers *Save in keyring*."""
        super().__init__(**kwargs)
        self.prompt = prompt
        self.entry.entry.password = True
        self.keep.visible = can_keep

    def accept(self) -> tuple[str, bool]:
        """``(password, keep)``; Cancel answers None."""
        return self.entry.value, bool(self.keep.value & 1) and self.keep.visible
