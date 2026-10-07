"""Options > Colors, Store palette and Load palette: DOS Navigator's
``ChangeColors``, ``StoreColors`` and ``LoadColors``, the palette as .nss."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent
from navkit.stylesheet import parse, variables_in

from navigator.__main__ import Navigator
from navigator.palette import (
    DERIVED, ENTRIES, NAVIGATOR_GROUP, differences, entry_values, groups, palette_path, read_palette,
    render_palette, save_palette, user_themes,
)
from navigator.scheme import load_scheme, theme_names, theme_path, user_scheme
from navigator.widgets.shell.commands import ChangeColors, LoadColors, StoreColors


def test_inherit_drops_a_declaration_so_the_field_cascades():
    sheet = parse("$b: inherit; A { bold: true } A.x { fg: red; bold: $b } A.y { bold: inherit; italic: true }")
    assert [rule.declarations for rule in sheet.rules] == [{"bold": True}, {"fg": 1}, {"italic": True}]


def test_the_groups_are_dns_runs_and_navigators_own_last():
    found = groups()
    assert found[0] == ("Timer", [("desktop", "Color")])
    assert [name for name, _ in found].count("Tree") == 2
    assert found[-1][0] == NAVIGATOR_GROUP and [stem for stem, _ in found[-1][1]] == list(DERIVED)
    assert sum(len(items) for _, items in found) == len(ENTRIES) + len(DERIVED)


def test_a_rendered_palette_reads_back_as_it_was_written():
    values = {"panel-fg": "#102030", "panel-bold": "true", "desktop-bg": "default", "image-italic": "inherit"}
    text = render_palette(values, "mine")
    assert variables_in(text) == values
    assert text.index("$desktop-bg") < text.index("$panel-fg") < text.index("$image-italic")


def test_every_entry_has_its_seven_and_the_directory_is_bold():
    values = entry_values(load_scheme("default").variables)
    assert len(values) == 7 * (len(ENTRIES) + len(DERIVED))
    assert values["directory-bold"] == "true" and values["cursor-bold"] == "inherit"
    assert values["marked-bold"] == "false"


def test_the_user_palette_goes_over_the_theme_and_a_broken_one_is_left_out():
    save_palette({"panel-fg": "#ff0000"})
    sheet, problem = user_scheme("default")
    assert problem is None and sheet.variables["panel-fg"] == "#ff0000"
    palette_path().write_text("$panel-fg: nonsense;")
    sheet, problem = user_scheme("default")
    assert problem and sheet.variables["panel-fg"] == load_scheme("default").variables["panel-fg"]
    save_palette({})
    assert not palette_path().exists()


def test_a_stored_theme_is_one_by_name_and_wins_over_a_shipped_one():
    user_themes().mkdir(parents=True)
    (user_themes() / "mine.nss").write_text("$panel-fg: red;")
    (user_themes() / "default.nss").write_text("$panel-fg: red;")
    assert "mine" in theme_names()
    assert theme_path("default") == user_themes() / "default.nss"


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    return tmp_path


def navigator(path: Path) -> Navigator:
    app = Navigator(path, path, load_scheme("default"), terminal=FakeTerminal(80, 25))
    return app


def colors_open(a) -> bool:
    return a.modal is not None and getattr(a.modal, "title", None) == "Colors"


def open_colors(a):
    a.spawn(a.run_command(ChangeColors))


def test_a_colour_picked_paints_at_once_and_cancel_puts_it_back(place):
    app = navigator(place)
    before = app.shell.stylesheet.variables["desktop-fg"]
    seen = {}
    run_app(app, [open_colors, Until(colors_open, timeout=5),
                  lambda a: seen.update(shown=a.modal.stem, color=a.modal.foreground.color),
                  lambda a: a.modal.foreground.focus(), KeyEvent("right"), lambda a: None,
                  lambda a: seen.update(live=a.shell.stylesheet.variables["desktop-fg"],
                                        line=a.modal.foreground_value.value),
                  KeyEvent("escape"), lambda a: None,
                  lambda a: seen.update(after=a.shell.stylesheet.variables["desktop-fg"])])
    assert seen["shown"] == "desktop" and seen["color"] == 1  # DEFAULT.PAL's blue
    assert seen["live"] == "green" and seen["line"] == "green"
    assert seen["after"] == before
    assert not palette_path().exists()


def test_ok_keeps_what_differs_from_the_theme_true_colour_and_attributes_among_it(place):
    app = navigator(place)
    seen = {}

    def edit(a):
        box = a.modal
        box.groups.cursor = [name for name, _ in box.groups_of].index("File Panel")
        seen["group"] = True

    def pick_item(a):
        box = a.modal
        seen["items"] = list(box.items.items)
        box.items.cursor = 0

    def change(a):
        box = a.modal
        seen["stem"] = box.stem
        box.background_value.value = "#203040"
        box.attributes.toggle(0)  # Bold: [?] -> [X]
        box.attributes.toggle(2)  # Italic: [?] -> [X]
        box.attributes.toggle(2)  # Italic: [X] -> [ ]

    run_app(app, [open_colors, Until(colors_open, timeout=5), edit, lambda a: None, pick_item, lambda a: None,
                  change, lambda a: None,
                  lambda a: seen.update(colour=a.modal.background.color, sample=a.modal.sample.sample),
                  KeyEvent("enter"), Until(lambda a: palette_path().exists(), timeout=5),
                  lambda a: seen.update(live=a.shell.stylesheet.variables.get(f"{seen['stem']}-bg"))])
    stem = seen["stem"]
    assert read_palette(palette_path()) == {f"{stem}-bg": "#203040", f"{stem}-bold": "true",
                                            f"{stem}-italic": "false"}
    assert seen["colour"] == -1 and seen["sample"].bg == (0x20, 0x30, 0x40) and seen["sample"].bold
    assert seen["live"] == "#203040"


def test_store_palette_writes_every_entry_and_load_palette_takes_one_back(place):
    app = navigator(place)

    def name_it(a):
        a.modal.target.value = "mine"

    run_app(app, [lambda a: a.spawn(a.run_command(StoreColors)),
                  Until(lambda a: getattr(a.modal, "title", None) == "Store Color Palette", timeout=5),
                  name_it, KeyEvent("enter"),
                  Until(lambda a: (user_themes() / "mine.nss").exists(), timeout=5)])
    stored = read_palette(user_themes() / "mine.nss")
    assert stored == entry_values(load_scheme("default").variables)
    assert "mine" in theme_names()

    (user_themes() / "red.nss").write_text("$panel-fg: red; $panel-underline: true;")
    app = navigator(place)

    def choose(a):
        a.modal.target.value = str(user_themes() / "red.nss")

    run_app(app, [lambda a: a.spawn(a.run_command(LoadColors)),
                  Until(lambda a: getattr(a.modal, "title", None) == "Load Color Palette", timeout=5),
                  choose, KeyEvent("enter"), Until(lambda a: palette_path().exists(), timeout=5),
                  lambda a: None])
    assert read_palette(palette_path()) == {"panel-fg": "red", "panel-underline": "true"}
    assert app.shell.stylesheet.variables["panel-fg"] == "red"


def test_a_file_that_is_not_a_palette_is_said_so(place):
    user_themes().mkdir(parents=True)
    (user_themes() / "bad.nss").write_text("$panel-fg: nonsense;")
    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: a.spawn(a.run_command(LoadColors)),
                  Until(lambda a: getattr(a.modal, "title", None) == "Load Color Palette", timeout=5),
                  lambda a: setattr(a.modal.target, "value", str(user_themes() / "bad.nss")), KeyEvent("enter"),
                  Until(lambda a: getattr(a.modal, "title", None) == "Error", timeout=5),
                  lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter")])
    assert seen["prompt"].startswith("Not a palette") and not palette_path().exists()


def test_differences_are_what_the_palette_keeps():
    assert differences({"a": "1", "b": "2"}, {"a": "1", "b": "3", "c": "4"}) == {"b": "3", "c": "4"}


def test_the_selector_walks_as_turbo_visions_did():
    from conftest import awaited
    from navml.widgets.dialog.color_selector import ColorSelector

    grid = ColorSelector(width=12, height=4)
    walk = []
    for start, key in ((0, "left"), (15, "right"), (5, "up"), (0, "up"), (2, "up"), (15, "down"), (13, "down"),
                       (-1, "right")):
        grid.color = start
        awaited(grid.on_key(KeyEvent(key)))
        walk.append(grid.color)
    assert walk == [15, 0, 1, 15, 13, 0, 2, 1]
