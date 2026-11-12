"""A setup page whose controls say which setting each edits: ``key: "temp_dir"``.

Each page of Options > Configuration seeded every control from its section
in ``__init__`` -- the value, converted, and the setting's comment as the
tooltip -- and converted every one back in ``accept()``.  A page extending
:class:`SettingsPage` says only ``key:`` on each control in its markup, and
this does both, the conversion read off the control's kind and the
setting's own declaration (``navigator.settings.Setting``):

=================  =============================  ==============================
control            setting                        value
=================  =============================  ==============================
``CheckBoxes``     a bit group (``OPTIONS``)      ``to_bits`` / ``from_bits``,
                                                  a tooltip a box
``CheckBoxes``     one ``bool``                   1 or 0
``RadioButtons``   ``choices``                    the index of the choice
``MaskedField``    ``int``                        zero-padded to the mask; a
                                                  blank place counts as nought
``Field``          ``str``                        as written, stripped
=================  =============================  ==============================

A key is a setting of the page's own section (:attr:`section_name`), or
``"section.name"`` for another.  A control whose value needs more than this
-- a language list made at run time, a floor of 1 -- is still seeded and read
in the page's own half, which may override :meth:`accept` and add to what it
answers.  navml knows nothing of this: ``key`` is only a name to it.
"""

from __future__ import annotations

from typing import Any, Iterator, Mapping

from navkit.widget import Widget

from navml.component import Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.masked_field import MaskedField
from navml.widgets.dialog.radio_buttons import RadioButtons

from navigator.settings import SETTINGS, Section


class SettingsPage(Component):
    """A page seeding its keyed controls from the settings when it is built,
    and answering their values, converted back, from :meth:`accept`."""

    #: The section a bare ``key`` names: ``class section_name: "system"``.
    section_name: str = ""

    def __init__(
        self,
        section: Section | None = None,
        sections: Mapping[str, Section] | None = None,
        **kwargs: Any,
    ) -> None:
        #: Sections other than :data:`SETTINGS`' to seed from and judge by --
        #: a test's, say -- by name; the page's own one may come as *section*.
        self._sections = dict(sections or {})
        if section is not None:
            self._sections[self.section_name] = section
        super().__init__(**kwargs)

    @property
    def section(self) -> Section:
        """The page's own section."""
        return self.section_of(self.section_name)

    def section_of(self, name: str) -> Section:
        """Section *name*, this page's own copy if it was given one."""
        return self._sections.get(name) or SETTINGS.section(name)

    def built(self) -> None:
        super().built()
        for control, section, name in self.keyed():
            _seed(control, section, name)

    def keyed(self) -> Iterator[tuple[Widget, Section, str]]:
        """Every control with a ``key``, its section and its setting's name."""
        stack = list(self.children)
        while stack:
            widget = stack.pop(0)
            key = getattr(widget, "key", "")
            if isinstance(key, str) and key:
                where, dot, name = key.rpartition(".")
                yield widget, self.section_of(where if dot else self.section_name), name
                continue
            stack[0:0] = widget.children

    def accept(self) -> dict[str, Any]:
        """The keyed controls' values: ``{name: value}`` when they are all the
        page's own section's, else ``{section: {name: value}}``."""
        answer: dict[str, dict[str, Any]] = {}
        for control, section, name in self.keyed():
            answer.setdefault(section.name, {}).update(_read(control, section, name))
        if set(answer) <= {self.section_name}:
            return answer.get(self.section_name, {})
        return answer


def _seed(control: Any, section: Section, name: str) -> None:
    group = _group(section, name)
    if isinstance(control, CheckBoxes) and group is not None:
        control.value = section.to_bits(group)
        control.tooltips = type(section).tooltips(group)
        return
    field = _field(section, name)
    value = getattr(section, name)
    control.tooltip = type(section).tooltip(name)
    if isinstance(control, CheckBoxes) and isinstance(field.default, bool):
        control.value = 1 if value else 0
        # On the box itself too, where the pointer hovers it.
        control.tooltips = [control.tooltip]
    elif isinstance(control, RadioButtons) and field.choices is not None:
        # The keyboard starts on the choice made, as ``TRadioButtons``' did.
        control.value = control.sel = field.choices.index(value)
    elif isinstance(control, MaskedField) and isinstance(field.default, int):
        width = _width(control)
        control.value = f"{min(10 ** width - 1, max(0, value)):0{width}d}"
    elif isinstance(field.default, str) and field.choices is None:
        control.value = value
    else:
        raise TypeError(
            f"{type(control).__name__} key {name!r}: no conversion for a "
            f"{type(field.default).__name__} setting on this kind of control"
        )


def _read(control: Any, section: Section, name: str) -> dict[str, Any]:
    group = _group(section, name)
    if isinstance(control, CheckBoxes) and group is not None:
        return Section.from_bits(group, control.value)
    field = _field(section, name)
    if isinstance(control, CheckBoxes):
        return {name: bool(control.value & 1)}
    if isinstance(control, RadioButtons):
        return {name: field.choices[control.value]}
    if isinstance(control, MaskedField):
        text = control.value.replace(" ", "0")
        return {name: int(text) if text.isdigit() else getattr(section, name)}
    return {name: control.value.strip()}


def _group(section: Section, name: str) -> tuple[str, ...] | None:
    """The bit group *name* is (``OPTIONS``), or None for a single setting."""
    value = getattr(type(section), name, None) if name.isupper() else None
    return value if isinstance(value, tuple) else None


def _field(section: Section, name: str) -> Any:
    field = type(section).field(name)
    if field is None:
        raise KeyError(f"[{section.name}] has no setting {name!r}")
    return field


def _width(control: MaskedField) -> int:
    """How many digits the mask holds: ``"999"`` is three."""
    return max(1, sum(1 for c in control.mask if c == "9"))


__all__ = ["SettingsPage"]
