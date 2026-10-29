"""File > Compare files: two files side by side (``DiffWindow``, ``DiffView``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.widgets.viewer.diff_window import DiffWindow


@pytest.fixture
def sides(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for side in ("west", "east"):
        (tmp_path / side).mkdir()
    lines = [f"line {n}" for n in range(60)]
    changed = list(lines)
    changed[5] = "line five"
    del changed[30]
    changed.insert(50, "a new line")
    (tmp_path / "west" / "a.txt").write_text("\n".join(lines) + "\n")
    (tmp_path / "east" / "a.txt").write_text("\n".join(changed) + "\n")
    (tmp_path / "west" / "b.txt").write_text("other\n")
    (tmp_path / "west" / "same.txt").write_text("same\n")
    (tmp_path / "east" / "same.txt").write_text("same\n")
    (tmp_path / "east" / "bin").write_bytes(b"\0\1")
    return tmp_path


def navigator(sides: Path) -> Navigator:
    return Navigator(sides / "west", sides / "east", terminal=FakeTerminal(100, 30))


def put_cursor(app, name: str, panel=None) -> None:
    panel = panel or app.manager.active_panel
    panel.cursor = next(i for i, item in enumerate(panel.items) if item.name == name)


def diff(app) -> None:
    app.manager.spawn(app.manager.diff_files())


def window(app) -> DiffWindow | None:
    return next((w for w in app.shell.desktop.windows() if isinstance(w, DiffWindow)), None)


def test_the_cursor_file_is_compared_with_its_namesake_and_opens_on_the_first_difference(sides):
    app = navigator(sides)
    seen = {}

    def look(a):
        view = window(a).view
        seen.update(hunks=view.model.hunks, current=view.current, top=view.top, info=view.info_text,
                    titles=(view.left_title, view.right_title))

    run_app(app, [lambda a: put_cursor(a, "a.txt"), diff, Until(window), look])
    assert seen["hunks"] == (5, 30, 51)
    assert seen["current"] == 0 and seen["top"] == 3
    assert "Difference 1 of 3" in seen["info"] and "+1 -1 ~1" in seen["info"]
    assert seen["titles"] == (str(sides / "west" / "a.txt"), str(sides / "east" / "a.txt"))


def test_n_and_p_go_from_difference_to_difference_and_both_sides_scroll_as_one(sides):
    app = navigator(sides)
    seen = []

    def note(a):
        view = window(a).view
        seen.append((view.current, view.top, view.x_delta))

    run_app(app, [lambda a: put_cursor(a, "a.txt"), diff, Until(window), KeyEvent("n"), note,
                  KeyEvent("down", alt=True), note, KeyEvent("n"), note, KeyEvent("p"), note,
                  KeyEvent("pagedown"), KeyEvent("right"), note])
    assert seen[0][:2] == (1, 28)
    assert seen[1][0] == 2
    assert seen[2][0] == 2  # nothing after the last: the bell, and nothing moved
    assert seen[3][0] == 1
    current, top, x_delta = seen[4]
    assert current == 1 and top > seen[3][1] and x_delta == 1


def test_a_changed_line_is_painted_in_its_class_on_both_sides(sides):
    app = navigator(sides)
    seen = {}

    def look(a):
        view = window(a).view
        seen.update(changed=view.part_style("line", classes=("changed",)), plain=view.style)

    run_app(app, [lambda a: put_cursor(a, "a.txt"), diff, Until(window), look])
    assert seen["changed"] != seen["plain"]


def test_two_tagged_files_in_one_panel_are_compared_with_each_other(sides):
    app = navigator(sides)
    seen = {}

    def tag(a):
        a.manager.left.marked = frozenset({"a.txt", "b.txt"})

    run_app(app, [tag, lambda a: seen.update(pair=a.manager._diff_pair())])
    left, right = seen["pair"]
    assert (left.name, right.name) == ("a.txt", "b.txt")
    assert left.path.parent == right.path.parent == sides / "west"


def test_without_a_namesake_the_other_cursor_file_is_taken(sides):
    app = navigator(sides)
    seen = {}

    def go(a):
        put_cursor(a, "b.txt")
        put_cursor(a, "bin", a.manager.right)
        seen.update(pair=a.manager._diff_pair())

    run_app(app, [go])
    assert [place.name for place in seen["pair"]] == ["b.txt", "bin"]


def test_the_same_files_and_binary_ones_are_said_in_a_box(sides):
    app = navigator(sides)
    seen = {}

    def other_bin(a):
        put_cursor(a, "b.txt")
        put_cursor(a, "bin", a.manager.right)

    run_app(app, [lambda a: put_cursor(a, "same.txt"), diff, Until(lambda a: a.modal is not None),
                  lambda a: seen.update(same=a.modal.prompt), KeyEvent("enter"),
                  other_bin, diff, Until(lambda a: a.modal is not None),
                  lambda a: seen.update(binary=a.modal.prompt), KeyEvent("enter"),
                  lambda a: seen.update(window=window(a))])
    assert "identical" in seen["same"]
    assert "byte 0" in seen["binary"]
    assert seen["window"] is None


def test_nothing_to_compare_greys_the_menu_entry(sides):
    from navigator.widgets.manager.commands import DiffFiles

    app = navigator(sides)
    seen = {}

    def look(a):
        a.manager.left.cursor = 0
        seen.update(enabled=a.manager.enables(DiffFiles()), first=a.manager.left.selected.name)

    run_app(app, [look])
    assert seen["first"] == ".." and seen["enabled"] is False


def test_hebrew_in_compared_files_reads_the_right_way_round():
    from conftest import settle
    from navkit.bidi import layout
    from navkit.screen import ScreenBuffer
    from navkit.widget import Widget
    from navigator.lib.file_ops.filediff import align
    from navigator.widgets.viewer.diff_view.diff_view import DiffView

    root = Widget(width=41, height=4)
    view = root.add(DiffView(x=0, y=0, width=41, height=4))
    view.model = align("שלום abc\n".encode(), "שלום abd\n".encode())
    settle()
    buffer = ScreenBuffer(41, 4)
    view.render(buffer)

    def text(x, width):
        return "".join(buffer.get(column, 1)[0] for column in range(x, x + width)).rstrip()

    assert text(1, 19) == "".join(cell for _, cell in layout("שלום abc"))
    assert text(22, 19) == "".join(cell for _, cell in layout("שלום abd"))
