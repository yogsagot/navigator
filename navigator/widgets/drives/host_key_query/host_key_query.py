"""What it answers: ``"once"``, ``"save"``, or None."""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr
from navkit.reactive import unbind

from navml.widgets.dialog.button import Button
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog


class HostKeyQuery(Dialog):
    """Trust an unknown server's key: once, saved, or not."""

    def __init__(self, host: str = "", key_type: str = "", fingerprint: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.prompt = tr("The authenticity of host {host} can't be established.\n"
                         "{type} key fingerprint is\n{fingerprint}").format(
            host=escape_caption(host), type=escape_caption(key_type), fingerprint=escape_caption(fingerprint))
        unbind(self.ok, Button.text)
        self.ok.text = tr("~A~ccept")
        unbind(self.no, Button.text)
        self.no.text = tr("~S~ave")

    def accept(self) -> str:
        return "once"

    def close(self, result: Any = None) -> None:
        """*No* -- captioned *Save* here -- answers False: that is *save*."""
        super().close("save" if result is False else result)
