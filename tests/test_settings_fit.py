"""Every caption on every page of Options > Settings fits its control, in every
language Navigator ships: a translation longer than its English is cut off
silently otherwise (*Return to last cursor position* lost its last letters in
English itself, *Automatic (the one running)* in every language)."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit import i18n
from navigator.__main__ import Navigator
from tools.fitcheck import LANGUAGES, clipped


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
