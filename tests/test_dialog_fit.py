"""Every dialog and window that can be made with no arguments fits its captions,
in every language Navigator ships (``tools/fitcheck.py``'s bare pass).

The boxes that need arguments -- a copy's files, a viewer's file -- are what the
screenshot scenes open; ``tools/fitcheck.py --check`` measures those as well,
too slow for every run of the suite.  ``tests/test_settings_fit.py`` covers the
Settings box page by page."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit import i18n
from navigator.__main__ import Navigator
from tools.fitcheck import LANGUAGES, NOT_BARE, classes, open_and_measure


@pytest.mark.parametrize("code", LANGUAGES)
def test_no_caption_is_cut_off_in_a_dialog_made_bare(code, tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)
    # The shipped catalogues: the suite speaks English with none.
    i18n.register_package("navml.locales")
    i18n.register_package("navigator.locales")
    i18n.LOCALE.code = code
    names = sorted(set(classes()) - NOT_BARE)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(84, 30))
    found: list[str] = []
    made: list[str] = []

    def measure(a):
        async def run():
            more, failed = await open_and_measure(a, names)
            found.extend(more)
            made.extend(name for name in names if name not in failed)
        return a.spawn(run())

    run_app(app, [measure, Until(lambda a: bool(made), timeout=60)])
    # Most can be made bare; the check is no check if none were.
    assert len(made) > 40, made
    assert not found, "\n".join(found)


@pytest.mark.parametrize("code", LANGUAGES)
def test_the_menu_bar_menus_key_bar_and_headings_fit_80_columns(code, tmp_path, monkeypatch):
    """The screen's own lines on an 80-column terminal: the menu bar not run
    under the clock, no menu box wider than the screen, no F-key left off the
    key bar (Latvian lost F8 and F10 there, Russian F10), every column heading
    within its column -- with the panels in front, a viewer, and an editor."""
    from tools.fitcheck import chrome_everywhere

    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)
    i18n.register_package("navml.locales")
    i18n.register_package("navigator.locales")
    i18n.LOCALE.code = code
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    found: list[str] = []
    done: list[bool] = []

    def measure(a):
        async def run():
            found.extend(await chrome_everywhere(a, tmp_path))
            done.append(True)
        return a.spawn(run())

    run_app(app, [measure, Until(lambda a: bool(done), timeout=20)])
    assert not found, "\n".join(found)


def test_a_key_bar_that_loses_an_f_key_even_tight_drops_the_blank_after_each_key(tmp_path, monkeypatch):
    """The Latvian editor's nine items do not fit 80 columns with a blank
    between key and caption; the row keeps them all as ``F2Saglab.``."""
    from navigator.lib.config.file_history import open_editor
    from navkit.screen import ScreenBuffer

    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)
    i18n.register_package("navml.locales")
    i18n.register_package("navigator.locales")
    i18n.LOCALE.code = "lv"
    (tmp_path / "a.txt").write_text("text\n")
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = {}

    def look(a):
        bar = a.shell.keybar
        buffer = ScreenBuffer(bar.width, 1)
        bar.render(buffer)
        seen["row"] = "".join(buffer.get(x, 0)[0] or " " for x in range(bar.width))
        seen["keys"] = [key for key, *_ in bar.items()]

    run_app(app, [lambda a: a.spawn(open_editor(a.shell.desktop, tmp_path / "a.txt")),
                  Until(lambda a: a.shell.desktop.active_window is not a.manager), look])
    assert "f10" in seen["keys"] and "f1" in seen["keys"]
    assert seen["row"].startswith("F1Palīdz.") and "F10Izvēlne" in seen["row"]
