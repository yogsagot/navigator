"""The handlers behind ``encrypt_dialog.nml``: what it opens on, what OK
refuses, and gpg's keys in a box.

It opens on the program, method, recipients and options last accepted, kept in
``navigator.ini``'s ``[encryption]`` -- never the passphrase.  A program that is
not installed cannot be chosen.
"""

from __future__ import annotations

import asyncio
from typing import Any

from navkit.events import Event
from navkit.i18n import tr

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.file_ops import encrypt
from navigator.settings import SETTINGS, EncryptionData


class EncryptDialog(Dialog):
    """*Encrypt Files*: gpg or age, to a passphrase or to recipients, armored
    or not, the originals kept or removed."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        section = SETTINGS.encryption
        installed = encrypt.available()
        self.tool.enable_mask = sum(1 << index for index, tool in enumerate(EncryptionData.TOOLS)
                                    if tool in installed)
        self.tool.tooltips = [
            "" if tool in installed else tr("{program} is not installed: install the {package} package").format(
                program=tool, package=encrypt.PACKAGES[tool])
            for tool in EncryptionData.TOOLS]
        tool = section.tool if section.tool in installed else (installed[0] if installed else section.tool)
        self.tool.value = self.tool.sel = EncryptionData.TOOLS.index(tool)
        self.method.value = self.method.sel = EncryptionData.METHODS.index(section.method)
        self.passphrase.entry.password = True
        self.confirm.entry.password = True
        self.recipients.value = section.recipients
        self.options.value = (1 if section.armor else 0) | (2 if section.delete_originals else 0)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon)

    def problem(self) -> str:
        """Why OK cannot close the box now, ``""`` when it can."""
        tool = EncryptionData.TOOLS[self.tool.value]
        if not self.tool.item_enabled(self.tool.value):
            return tr("{program} is not installed").format(program=tool)
        if EncryptionData.METHODS[self.method.value] == "passphrase":
            if not self.passphrase.value:
                return tr("Type a passphrase.")
            if self.passphrase.value != self.confirm.value:
                return tr("The passphrases do not match.")
            return ""
        return "" if self.recipients.value.split() else tr("Name at least one recipient.")

    def accept(self) -> dict[str, Any] | None:
        """``{"tool", "method", "passphrase", "recipients", "armor",
        "delete_originals"}``; None while :meth:`problem` says why not."""
        if self.problem():
            return None
        method = EncryptionData.METHODS[self.method.value]
        return {
            "tool": EncryptionData.TOOLS[self.tool.value],
            "method": method,
            "passphrase": self.passphrase.value if method == "passphrase" else None,
            "recipients": self.recipients.value.split() if method == "recipients" else [],
            "armor": bool(self.options.value & 1),
            "delete_originals": bool(self.options.value & 2),
        }

    async def on_pick_click(self, event: Event) -> bool:
        problem = self.problem()
        if problem:
            self.spawn(self._say(problem))
            return True
        if EncryptionData.METHODS[self.method.value] == "recipients":
            self.record_history()
        self.close(self.accept())
        return True

    async def _say(self, problem: str) -> None:
        await Dialog(title=tr("Error"), prompt=problem, buttons="ok").execute(self.application)

    async def on_choose_keys_click(self, event: Event) -> bool:
        self.spawn(self._choose_key())
        return True

    async def _choose_key(self) -> None:
        """gpg's keys that can encrypt, in a box over the dialog; the one
        chosen added to the recipients by its fingerprint."""
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        app = self.application
        keys = await asyncio.to_thread(encrypt.list_gpg_keys)
        if not keys:
            await self._say(tr("gpg has no key to encrypt to."))
            return
        menu = SubMenu()
        items = [menu.add_item(escape_caption(f"{uid or fingerprint}  {fingerprint[-16:]}"))
                 for fingerprint, uid in keys]
        title = tr("Keys")
        width, height = PopupMenu.measure(menu, app, self, title)
        ox, oy = self.offset()
        x = ox + self.x + max(0, (self.width - width) // 2)
        y = oy + self.y + max(0, (self.height - height) // 2)
        chosen = await PopupMenu(menu, x, y, current=0, behind=self, title=title).execute(app)
        if chosen is None:
            return
        fingerprint = keys[items.index(chosen)][0]
        names = self.recipients.value.split()
        if fingerprint not in names:
            self.recipients.value = " ".join([*names, fingerprint])
        self.recipients.focus()
