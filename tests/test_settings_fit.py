"""Every caption on every page of Options > Settings fits its control, in every
language Navigator ships: a translation longer than its English is cut off
silently otherwise (*Return to last cursor position* lost its last letters in
English itself, *Automatic (the one running)* in every language)."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit import i18n
from navkit.bidi import display_width
from navigator.__main__ import Navigator

LANGUAGES = ("en", "he", "ar", "ja", "lv", "ru", "zh")


def _plain(text: str) -> str:
    from navml.widgets.dialog.control.control import parse_shortcut

    return parse_shortcut(text or "")[0]


def clipped(widget, where: str) -> list[str]:
    """What under *widget* is wider than the room it has: a check box's or
    radio button's caption, a label, a choice a line drops."""
    from navml.widgets.dialog.choice_line.choice_line import ChoiceLine
    from navml.widgets.dialog.cluster.cluster import Cluster
    from navml.widgets.dialog.label import Label
    from navml.widgets.dialog.static_text import StaticText

    found: list[str] = []
    if not widget.visible:
        return found
    if isinstance(widget, Cluster):
        rows = max(1, widget.height)
        for index, item in enumerate(widget.items):
            # ``[x]``, a blank, then the caption, from where its column starts.
            need = widget.column_x(index // rows) + 4 + display_width(_plain(item))
            if need > widget.width:
                found.append(f"{where}: {_plain(item)!r} needs {need} columns, has {widget.width}")
    elif isinstance(widget, ChoiceLine):
        button = next((child for child in widget.parent.children if hasattr(child, "choices")), None)
        for choice in getattr(button, "choices", None) or []:
            # A blank either side of the text, as an input line has.
            if display_width(choice) > widget.width - 2:
                found.append(f"{where}: choice {choice!r} needs {display_width(choice)}, has {widget.width - 2}")
    elif isinstance(widget, (Label, StaticText)) and widget.height <= 1:
        text = _plain(getattr(widget, "text", ""))
        if "\n" not in text and display_width(text) > widget.width:
            found.append(f"{where}: {text!r} needs {display_width(text)} columns, has {widget.width}")
    for child in widget.children:
        found.extend(clipped(child, where))
    return found


@pytest.mark.parametrize("code", LANGUAGES)
def test_no_settings_caption_is_cut_off(code, tmp_path, monkeypatch):
    from navigator.widgets.setup.settings_dialog import SettingsDialog
    from navigator.widgets.setup.settings_dialog.settings_dialog import PAGES

    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)
    # The shipped catalogues: the suite speaks English with none.
    i18n.register_package("navml.locales")
    i18n.register_package("navigator.locales")
    i18n.LOCALE.code = code
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(84, 30))
    dialog = SettingsDialog("system", side="top")
    found: list[str] = []

    def show(tab):
        return lambda a: dialog.tabs.select(dialog.tabs.index_of(dialog.page(tab)))

    def look(tab):
        return lambda a: found.extend(clipped(dialog.page(tab), f"{code} {tab}"))

    steps = [lambda a: a.spawn(dialog.execute(a)), Until(lambda a: a.modal is dialog)]
    for tab in PAGES:
        steps += [show(tab), look(tab)]
    run_app(app, steps)
    assert not found, "\n".join(found)
