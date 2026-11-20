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
