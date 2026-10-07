"""What the Colors dialog edits, and what OK means: every entry's variables.

The dialog holds a ``{variable: value}`` dict of every entry's seven -- the
two colours and :data:`~navigator.palette.ATTRIBUTES` -- as the palette now
gives them, and each change goes into it and out to *apply*, so the screen
(the dialog among it) repaints in the palette being made, as DN's
``ExecuteDialog(D, Application^.GetPalette)`` edited the palette in place.
OK answers the dict; Cancel answers None, and whoever applied puts the sheet
back.

The controls are followed by effects rather than by their events, and each
effect writes into the entry the controls *show* (``_shown``), not the one
the item list's cursor is on: in the batch that moves the cursor the controls
still hold the old entry until ``_show`` runs, and an effect that read the
cursor could write one entry's colours into the next.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from navkit.reactive import effect
from navkit.style import Style
from navkit.stylesheet import StylesheetError, parse_value
from navml.widgets.dialog.color_selector import COLORS
from navml.widgets.dialog.dialog import Dialog

from navigator.palette import ATTRIBUTES, groups

#: Every attribute box may come back to ``[?]``: ``inherit``.
ALL_BOXES = (1 << len(ATTRIBUTES)) - 1


def colour_of(text: str) -> Any:
    """*text* as a ``Style`` colour, or raise ``ValueError`` for none."""
    try:
        value = parse_value("fg", text, {})
    except StylesheetError as error:
        raise ValueError(str(error)) from None
    if isinstance(value, bool):
        raise ValueError(f"{text!r} is not a colour")
    return value


class ColorsDialog(Dialog):
    """``TColorDialog`` over *values*, telling *apply* of every change."""

    def __init__(self, values: Mapping[str, str] | None = None,
                 apply: Callable[[dict[str, str]], None] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: Every entry's variables, as edited so far.
        self.values: dict[str, str] = dict(values or {})
        self.apply = apply
        #: ``[(group, [(stem, item), ...]), ...]``.
        self.groups_of = groups()
        #: The stem the controls show.
        self._shown: str | None = None
        self.groups.items = [name for name, _ in self.groups_of]
        self.attributes.tristate = ALL_BOXES
        self._list_items(0)

    def mounted(self) -> None:
        super().mounted()
        effect(self, ColorsDialog._follow_group)
        effect(self, ColorsDialog._follow_item)
        effect(self, ColorsDialog._follow_selectors)
        effect(self, ColorsDialog._follow_values)
        effect(self, ColorsDialog._follow_attributes)

    # -- the two lists --------------------------------------------------------------

    def _list_items(self, group: int) -> None:
        self._group = group
        self.items.items = [item for _, item in self.groups_of[group][1]]
        self.items.cursor = 0
        self._show(self.groups_of[group][1][0][0])

    def _follow_group(self) -> None:
        """``TColorGroupList.FocusItem``: the group's items, the first focused."""
        group = self.groups.cursor
        if group != self._group and 0 <= group < len(self.groups_of):
            self._list_items(group)

    def _follow_item(self) -> None:
        """``TColorItemList.FocusItem``: the item's colours in the controls."""
        items = self.groups_of[self._group][1]
        cursor = self.items.cursor
        if 0 <= cursor < len(items) and items[cursor][0] != self._shown:
            self._show(items[cursor][0])

    @property
    def stem(self) -> str | None:
        """The entry the controls show."""
        return self._shown

    def value(self, key: str) -> str:
        return self.values.get(f"{self._shown}-{key}", "inherit" if key in ATTRIBUTES else "default")

    def _show(self, stem: str) -> None:
        self._shown = stem
        fg, bg = self.value("fg"), self.value("bg")
        self.foreground.color = COLORS.index(fg) if fg in COLORS else -1
        self.background.color = COLORS.index(bg) if bg in COLORS else -1
        self.foreground_value.value = fg
        self.background_value.value = bg
        on = mixed = 0
        for bit, name in enumerate(ATTRIBUTES):
            state = self.value(name)
            if state == "inherit":
                mixed |= 1 << bit
            elif state == "true":
                on |= 1 << bit
        self.attributes.value = on
        self.attributes.mixed = mixed
        self._sample()

    # -- the controls into the entry ------------------------------------------------------

    def _set(self, key: str, text: str) -> None:
        name = f"{self._shown}-{key}"
        if self._shown is None or self.values.get(name) == text:
            return
        self.values[name] = text
        self._sample()
        if self.apply is not None:
            self.apply(dict(self.values))

    def _follow_selectors(self) -> None:
        """A colour picked in a grid: the entry's, and its line's."""
        for selector, line, key in ((self.foreground, self.foreground_value, "fg"),
                                    (self.background, self.background_value, "bg")):
            color = selector.color
            if color >= 0 and self.value(key) != COLORS[color]:
                line.value = COLORS[color]
                self._set(key, COLORS[color])

    def _follow_values(self) -> None:
        """A colour typed: the entry's once it reads as one, and the grid's
        mark on it, or on none for a colour the grid does not have."""
        for selector, line, key in ((self.foreground, self.foreground_value, "fg"),
                                    (self.background, self.background_value, "bg")):
            text = line.value.strip()
            if text == self.value(key):
                continue
            try:
                colour_of(text)
            except ValueError:
                continue
            selector.color = COLORS.index(text) if text in COLORS else -1
            self._set(key, text)

    def _follow_attributes(self) -> None:
        on, mixed = self.attributes.value, self.attributes.mixed
        for bit, name in enumerate(ATTRIBUTES):
            mask = 1 << bit
            self._set(name, "inherit" if mixed & mask else "true" if on & mask else "false")

    def _sample(self) -> None:
        """``TColorDisplay``: the entry as it would be drawn, ``inherit`` as off."""
        fields: dict[str, Any] = {}
        for key in ("fg", "bg"):
            try:
                fields[key] = colour_of(self.value(key))
            except ValueError:
                pass
        for name in ATTRIBUTES:
            fields[name] = self.value(name) == "true"
        self.sample.sample = Style(**fields)

    def accept(self) -> dict[str, str]:
        return dict(self.values)
