"""What the Key bindings dialog edits, and what OK means: every section's keys.

The dialog holds ``{section: {command: keys}}`` for every section of
:mod:`navigator.keybindings`, as bound when it opened, and changes only that
copy; OK answers it and Cancel answers None, so nothing is bound until the
dialog is done.  A key moved onto a command is asked about when another
command of the same table has it (and taken from that one), and when the
application's own table has it, since that table is looked at first.  A key
a table cannot take -- a chord whose first key is bound alone -- is refused
with the reason.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from navkit.commands import KeyTableError, key_label
from navkit.events import Event
from navkit.reactive import effect
from navml.widgets.dialog.dialog import Dialog

from navigator.keybindings import Assignment, Entry, Section
from navigator.widgets.setup.key_bindings_dialog.binding_list import keys_text


class KeyBindingsDialog(Dialog):
    """Every section's commands over *sections*, starting from *assignments*
    (each section's current keys when not given)."""

    def __init__(self, sections: Sequence[Section] = (),
                 assignments: Mapping[str, Assignment] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self.sections = list(sections)
        #: Every section's keys, as edited so far.
        self.assignments: dict[str, Assignment] = {
            section.name: dict((assignments or {}).get(section.name) or section.current())
            for section in self.sections
        }
        self._group = -1
        self.groups.items = [section.title for section in self.sections]
        if self.sections:
            self._list(0)

    def mounted(self) -> None:
        super().mounted()
        effect(self, KeyBindingsDialog._follow_group)
        effect(self, KeyBindingsDialog._follow_entry)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.rebind, self.append, self.unbind, self.restore, self.reset,
                self.pick, self.abandon)

    def accept(self) -> dict[str, Assignment]:
        return {name: dict(assignment) for name, assignment in self.assignments.items()}

    # -- the two lists --------------------------------------------------------------

    @property
    def section(self) -> Section | None:
        """The category the commands list shows."""
        return self.sections[self._group] if 0 <= self._group < len(self.sections) else None

    @property
    def entry(self) -> Entry | None:
        """The command under the cursor."""
        selected = self.bindings.selected
        return selected[0] if selected is not None else None

    def _list(self, group: int) -> None:
        self._group = group
        self.bindings.cursor = 0
        self._refresh()

    def _refresh(self) -> None:
        section = self.section
        if section is None:
            self.bindings.items = []
            return
        keys = self.assignments[section.name]
        self.bindings.items = [(entry, keys.get(entry.name, entry.defaults))
                               for entry in section.entries]
        self._describe()

    def _follow_group(self) -> None:
        group = self.groups.cursor
        if group != self._group and 0 <= group < len(self.sections):
            self._list(group)

    def _follow_entry(self) -> None:
        self.bindings.cursor  # the effect follows the cursor
        self._describe()

    def _describe(self) -> None:
        selected = self.bindings.selected
        if selected is None:
            self.detail.text = ""
            return
        entry, keys = selected
        text = f"{entry.title}: {keys_text(keys)}"
        if keys != entry.defaults:
            text += f"\nDefault: {keys_text(entry.defaults)}"
        self.detail.text = text

    def keys_of(self, entry: Entry) -> tuple[str, ...]:
        section = self.section
        return self.assignments[section.name].get(entry.name, entry.defaults)

    # -- changing a command's keys ------------------------------------------------------

    async def _ask(self, prompt: str) -> bool:
        answer = await Dialog(title="Key bindings", prompt=prompt,
                              buttons="yes-no").execute(self.application)
        return answer is True

    async def _refuse(self, prompt: str) -> None:
        await Dialog(title="Key bindings", prompt=prompt, buttons="ok").execute(self.application)

    def _put(self, assignment: Assignment) -> bool:
        """*assignment* as the section's, if its table can be made; else False."""
        section = self.section
        try:
            section.table(assignment)
        except KeyTableError as error:
            self.spawn(self._refuse(f"Cannot bind that:\n{error}"))
            return False
        cursor = self.bindings.cursor
        self.assignments[section.name] = assignment
        self._refresh()
        self.bindings.cursor = cursor
        self.bindings.focus()
        return True

    async def bind_key(self, entry: Entry, spec: str, replace: bool) -> bool:
        """*spec* onto *entry*: in place of its keys with *replace*, else
        beside them.  Whether it was bound."""
        section = self.section
        current = dict(self.assignments[section.name])
        label = key_label(spec)
        owner = next((other for other in section.entries if other.name != entry.name
                      and spec in current.get(other.name, other.defaults)), None)
        if owner is not None:
            if not await self._ask(f"{label} is bound to {owner.title}.\nReassign it?"):
                return False
            keys = current.get(owner.name, owner.defaults)
            current[owner.name] = tuple(key for key in keys if key != spec)
        if section.name != "global":
            outer = next((s for s in self.sections if s.name == "global"), None)
            if outer is not None:
                found = self.assignments[outer.name]
                shadow = next((e for e in outer.entries
                               if spec in found.get(e.name, e.defaults)), None)
                if shadow is not None and not await self._ask(
                        f"{label} is the global key for {shadow.title}, which is\n"
                        f"looked at first. Bind it here anyway?"):
                    return False
        keys = current.get(entry.name, entry.defaults)
        current[entry.name] = (spec,) if replace else (*(k for k in keys if k != spec), spec)
        return self._put(current)

    async def capture(self, replace: bool) -> None:
        """*Press a key*, then the key bound."""
        from navigator.widgets.setup.key_capture_dialog import KeyCaptureDialog

        entry = self.entry
        if entry is None:
            return
        spec = await KeyCaptureDialog().execute(self.application)
        if spec:
            await self.bind_key(entry, spec, replace)

    async def on_rebind_click(self, event: Event) -> bool:
        self.spawn(self.capture(replace=True))
        return True

    async def on_append_click(self, event: Event) -> bool:
        self.spawn(self.capture(replace=False))
        return True

    async def on_unbind_click(self, event: Event) -> bool:
        entry = self.entry
        if entry is not None:
            current = dict(self.assignments[self.section.name])
            current[entry.name] = ()
            self._put(current)
        return True

    async def on_restore_click(self, event: Event) -> bool:
        entry = self.entry
        if entry is not None:
            current = dict(self.assignments[self.section.name])
            current[entry.name] = entry.defaults
            self._put(current)
        return True

    async def on_reset_click(self, event: Event) -> bool:
        self.spawn(self.reset_all())
        return True

    async def reset_all(self) -> None:
        """Every command of every category back to its default keys."""
        if not await self._ask("Every key back to its default?"):
            return
        self.assignments = {section.name: section.defaults() for section in self.sections}
        self._refresh()
        self.bindings.focus()

    async def on_pick_click(self, event: Event) -> bool:
        self.close(self.accept())
        return True
