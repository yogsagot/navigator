"""The handlers behind ``forward_dialog.nml``: one port forward's lines.

OK answers a :class:`~navigator.lib.drives.forwards.Forward`, once the lines
make one (:meth:`ForwardDialog.valid` says why not, under them); Cancel
answers None.  A dynamic forward's destination lines are greyed: its SOCKS
client says where each connection goes."""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr
from navkit.reactive import effect, untracked

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives.forwards import KINDS, Forward


class ForwardDialog(Dialog):
    """One forward: its kind, where it listens, where it goes."""

    def __init__(self, forward: Forward | None = None, **kwargs: Any) -> None:
        """*forward* to edit, or None for a new local one."""
        super().__init__(**kwargs)
        if forward is not None:
            self.kind.value = self.kind.sel = KINDS.index(forward.kind)
            self.bind.value = forward.bind
            self.port.value = str(forward.port)
            self.host.value = forward.host
            self.host_port.value = str(forward.host_port) if forward.host_port else ""
        self._about()

    def mounted(self) -> None:
        super().mounted()
        effect(self, ForwardDialog._kind_changed)

    def _kind_changed(self) -> None:
        """Another kind: what it does said, a dynamic one's destination greyed."""
        self.kind.value
        with untracked():
            self._about()

    def _about(self) -> None:
        kind = KINDS[self.kind.value]
        dynamic = kind == "D"
        for line in (self.host, self.host_port):
            line.disabled = dynamic
        self.about.text = {
            "L": tr("A port here; each connection to it goes on to the destination as the server sees it."),
            "R": tr("A port on the server; each connection to it comes back to the destination as this "
                    "machine sees it."),
            "D": tr("A SOCKS proxy here; each connection goes where its program asks, from the server."),
        }[kind]

    def forward(self) -> Forward:
        """What the lines say.  Raises ``ValueError`` with why they are no forward."""
        kind = KINDS[self.kind.value]
        bind = self.bind.value.strip()
        if bind.startswith("[") and bind.endswith("]"):
            bind = bind[1:-1]
        port = self._port(self.port.value, tr("Type the port to listen on"), zero=True)
        if kind == "D":
            return Forward("D", port, bind)
        host = self.host.value.strip()
        if host.startswith("[") and host.endswith("]"):
            host = host[1:-1]
        if not host:
            raise ValueError(tr("Type the host to go to"))
        return Forward(kind, port, bind, host, self._port(self.host_port.value, tr("Type the port to go to")))

    @staticmethod
    def _port(text: str, missing: str, *, zero: bool = False) -> int:
        text = text.strip()
        if not text:
            raise ValueError(missing)
        if not text.isdigit() or not (0 if zero else 1) <= int(text) <= 65535:
            raise ValueError(tr("{text} is no port (1 to 65535)").format(text=text))
        return int(text)

    def valid(self) -> bool:
        try:
            self.forward()
        except ValueError as error:
            self.problem.text = escape_caption(str(error))
            return False
        return True

    def accept(self) -> Forward:
        return self.forward()


__all__ = ["ForwardDialog"]
