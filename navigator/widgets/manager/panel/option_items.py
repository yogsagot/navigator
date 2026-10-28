"""What a panel's option strip shows (``navml``'s ``OptionStrip``, as the
editor's and the viewer's -- ``navigator.widgets.editor.option_items``).

A departure, as those strips are: DN's panels showed none of this.  Hidden
files and the footer are switches, lit while on; the view mode and the order
are values, never lit, a click on one doing what Ctrl+Y and Alt+B do.

Each switch says whether *its* panel has it on (``lit``): ``Manager.checks``
answers about the active panel, and both panels show a strip.
"""

from __future__ import annotations

from typing import Any

from navkit.events import MouseClickEvent
from navkit.i18n import tr
from navml.widgets.option_strip import OptionItem, OptionStrip, option_label

from navigator.lib.appearance import icons
from navigator.widgets.manager.commands import SortBy, ToggleHidden, ToggleInfoLines, ToggleShowMode

#: Each switch's spelling at the Unicode and the Nerd tier.
HIDDEN_FILES = (".*", icons.OPTION_HIDDEN_FILES)
FOOTER = ("▁", icons.OPTION_FOOTER)


def _mode_label(panel: Any) -> str:
    return {"detailed": tr("Detailed"), "list": tr("List")}.get(panel.view_mode) or tr("Simple")


def _sort_label(panel: Any) -> str:
    """The order's caption as Alt+B's box has it, without its hot key, and the
    arrow of the way it runs."""
    from navigator.widgets.manager.manager.manager import sort_captions
    from navigator.widgets.manager.panel.panel import SORT_MODES

    mode = panel.sort_mode
    caption = dict(zip(SORT_MODES, sort_captions())).get(mode, mode).replace("~", "")
    return caption + panel.direction_arrow(mode, panel.sort_reverse)


def panel_items(panel: Any) -> tuple[OptionItem, ...]:
    """The panel's: Hidden files, the footer, the view mode and the order."""
    def switch(command: Any, word: Any, spellings: tuple[str, str], on: Any, tooltip: Any) -> OptionItem:
        return OptionItem(command, lambda: option_label(word(), spellings, panel.glyphs), lit=on,
                          tooltip=tooltip)

    return (
        switch(ToggleHidden, lambda: tr("Hid"), HIDDEN_FILES, lambda: panel.show_hidden,
               lambda: tr("Show hidden files")),
        switch(ToggleInfoLines, lambda: tr("Info"), FOOTER, lambda: panel.show_info,
               lambda: tr("Show the info lines")),
        OptionItem(ToggleShowMode, lambda: _mode_label(panel), lit=lambda: False,
                   tooltip=lambda: tr("View mode: simple, detailed or list")),
        OptionItem(SortBy, lambda: _sort_label(panel), lit=lambda: False,
                   tooltip=lambda: tr("Sort order")),
    )


class PanelOptionStrip(OptionStrip):
    """The strip on a panel's bottom frame.  A press on it makes its panel the
    active one first, as a press anywhere else on the panel does, so the
    command -- which acts on the active panel -- switches the panel clicked."""

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        panel = self.parent
        if (event.action == "press" and event.button == "left" and panel is not None
                and not panel.focused):
            panel.focus()
        return await super().on_mouse_click(event)
