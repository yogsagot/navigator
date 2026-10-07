"""What OK means in the editor: the variables as they are left, a dict."""

from __future__ import annotations

from typing import Any, Mapping

from navkit.events import Event
from navkit.reactive import effect
from navml.widgets.dialog.dialog import Dialog

from navigator.environ import valid_name


class EnvironmentDialog(Dialog):
    """DN's ``EditDOSEvironment``'s box over *variables*, sorted by name."""

    def __init__(self, variables: Mapping[str, str] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        #: ``[name, value]`` pairs, the list's order.
        self.pairs: list[list[str]] = [[name, value] for name, value in sorted((variables or {}).items())]
        self._shown: int | None = None
        self._refresh(0)

    def mounted(self) -> None:
        super().mounted()
        effect(self, EnvironmentDialog._follow_cursor)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.rename, self.append, self.delete, self.abandon)

    # -- the list and the value line ------------------------------------------------

    def _refresh(self, cursor: int) -> None:
        self._keep_value()
        self.names.items = [name for name, _ in self.pairs]
        self.names.cursor = max(0, min(cursor, len(self.pairs) - 1))
        self._show(self.names.cursor)

    def _keep_value(self) -> None:
        """What the value line holds, into the variable it shows (``SetValue``)."""
        if self._shown is not None and self._shown < len(self.pairs):
            self.pairs[self._shown][1] = self.value.value

    def _show(self, index: int) -> None:
        self._shown = index if index < len(self.pairs) else None
        self.value.value = self.pairs[index][1] if self._shown is not None else ""

    def _follow_cursor(self) -> None:
        """``TVarList.FocusItem``: the value kept, the next one shown."""
        cursor = self.names.cursor
        if cursor != self._shown:
            self._keep_value()
            self._show(cursor)

    def accept(self) -> dict[str, str]:
        self._keep_value()
        return {name: value for name, value in self.pairs}

    async def on_pick_click(self, event: Event) -> bool:
        self.close(self.accept())
        return True

    # -- the three that change the list -----------------------------------------------

    async def on_append_click(self, event: Event) -> bool:
        self.spawn(self.append_variable())
        return True

    async def append_variable(self) -> None:
        """``AppendVar``: *Add Environment Variable*, ``NAME=value``, put in
        where the cursor is."""
        from navigator.widgets.shell.edit_line_dialog import EditLineDialog

        box = EditLineDialog("", history="new_variable", caption="~V~ariable")
        box.title = "Add Environment Variable"
        text = await box.execute(self.application)
        name, _, value = (text or "").partition("=")
        name = name.strip()
        if not valid_name(name):
            return
        self._keep_value()
        self.pairs = [pair for pair in self.pairs if pair[0] != name]
        at = min(self.names.cursor, len(self.pairs))
        self.pairs.insert(at, [name, value])
        self._shown = None
        self._refresh(at)
        self.names.focus()

    async def on_rename_click(self, event: Event) -> bool:
        self.spawn(self.rename_variable())
        return True

    async def rename_variable(self) -> None:
        """``RenameVar``: *Rename variable "X"*, the value going with it."""
        from navigator.widgets.shell.edit_line_dialog import EditLineDialog

        index = self.names.cursor
        if index >= len(self.pairs):
            return
        old = self.pairs[index][0]
        box = EditLineDialog(old, history="new_variable", caption="~N~ew name")
        box.title = f'Rename variable "{old}"'
        new = ((await box.execute(self.application)) or "").strip()
        if not valid_name(new) or new == old:
            return
        self._keep_value()
        value = self.pairs[index][1]
        self.pairs = [pair for pair in self.pairs if pair[0] != new]
        index = next(i for i, pair in enumerate(self.pairs) if pair[0] == old)
        self.pairs[index] = [new, value]
        self._refresh(index)
        self.names.focus()

    async def on_delete_click(self, event: Event) -> bool:
        self.spawn(self.delete_variable())
        return True

    async def delete_variable(self) -> None:
        """``DeleteVar``: ``dlEnvDelConfirm``, then the variable gone."""
        index = self.names.cursor
        if index >= len(self.pairs):
            return
        name = self.pairs[index][0]
        answer = await Dialog(title="Confirm", prompt=f'OK to delete the Environment\nvariable "{name}"',
                              buttons="yes-no").execute(self.application)
        if answer is not True:
            return
        self._keep_value()
        del self.pairs[index]
        self._shown = None
        self._refresh(index)
        self.names.focus()
