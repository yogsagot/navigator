"""Disk > Directory sizes: ``navigator/widgets/shell/usage_window/``."""

from conftest import Until, run_app
from navkit.events import KeyEvent

from navigator.lib.file_ops import dirusage
from navigator.widgets.shell.usage_list.usage_list import UP


def fill(root):
    (root / "big").mkdir()
    (root / "big" / "inner").mkdir()
    (root / "big" / "inner" / "huge").write_bytes(b"x" * 300_000)
    (root / "big" / "file").write_bytes(b"x" * 50_000)
    (root / "small").mkdir()
    (root / "small" / "tiny").write_bytes(b"x" * 10)
    (root / "loose").write_bytes(b"x" * 100_000)
    return root


def window(app):
    return app.shell.desktop.active_window


def names(app):
    return [item.name for item in window(app).entries.items]


def usage_run(where, *actions, size=(100, 30)):
    """The window opened on the panels' *where*, read to the end, then *actions*."""
    from test_nav import navigator

    app = navigator(where, size=size)

    def open_it(a):
        from navigator.widgets.shell.commands import OpenUsageWindow

        a.spawn(a.run_command(OpenUsageWindow))

    def read(a):
        shown = window(a)
        return getattr(shown, "tree", None) is not None and not shown.scanning

    run_app(app, [open_it, Until(read), *actions, lambda a: None])
    return app


def test_the_window_lists_the_panels_directory_biggest_first(tmp_path):
    from navigator.widgets.shell.usage_window import UsageWindow

    seen = []

    def look(a):
        seen.append((type(window(a)), names(a), a.focused is window(a).entries))

    usage_run(fill(tmp_path), look)
    assert seen == [(UsageWindow, ["big", "loose", "small"], True)]


def test_enter_goes_down_and_backspace_back_up_to_the_same_row(tmp_path):
    seen = []

    def look(a):
        entries = window(a).entries
        seen.append((names(a), entries.selected.name))

    usage_run(fill(tmp_path), KeyEvent("enter"), look, KeyEvent("backspace"), look, KeyEvent("enter"), look,
              KeyEvent("left"), look)
    assert seen[0] == (["..", "inner", "file"], "..")
    assert seen[1] == (["big", "loose", "small"], "big")
    assert seen[2] == (["..", "inner", "file"], "..")
    assert seen[3] == (["big", "loose", "small"], "big")


def test_right_goes_down_and_dot_dot_goes_up(tmp_path):
    seen = []

    usage_run(fill(tmp_path), KeyEvent("right"), lambda a: seen.append(names(a)),
              KeyEvent("home"), KeyEvent("enter"), lambda a: seen.append(names(a)))
    assert seen == [["..", "inner", "file"], ["big", "loose", "small"]]
    assert UP.name == ".."


def test_the_sort_keys_and_the_same_key_again_turns_it_round(tmp_path):
    seen = []
    look = lambda a: seen.append(names(a))  # noqa: E731

    usage_run(fill(tmp_path), KeyEvent("n", ctrl=True), look, KeyEvent("n", ctrl=True), look,
              KeyEvent("s", ctrl=True), look, KeyEvent("s", ctrl=True), look)
    assert seen == [["big", "loose", "small"], ["small", "loose", "big"],
                    ["big", "loose", "small"], ["small", "loose", "big"]]


def test_ctrl_a_shows_the_apparent_size(tmp_path):
    seen = []

    def look(a):
        shown = window(a)
        seen.append((shown.apparent, shown.entries.apparent, shown.entries.whole == shown.tree.amount(shown.apparent)))

    usage_run(fill(tmp_path), look, KeyEvent("a", ctrl=True), look)
    assert seen == [(False, False, True), (True, True, True)]


def test_f8_erases_the_entry_and_takes_it_off_the_totals(tmp_path):
    fill(tmp_path)
    seen = []

    def before(a):
        shown = window(a)
        shown.entries.cursor = names(a).index("loose")
        seen.append(shown.tree.size)

    def after(a):
        shown = window(a)
        seen.append((names(a), shown.tree.size, shown.scanning))

    usage_run(tmp_path, before, KeyEvent("f8"), Until(lambda a: a.modal is not None), KeyEvent("enter"),
              Until(lambda a: not (tmp_path / "loose").exists()), Until(lambda a: "loose" not in names(a)), after)
    assert not (tmp_path / "loose").exists()
    assert seen[1] == (["big", "small"], seen[0] - 100_000, False)


def test_go_sends_the_panel_to_a_directory_and_closes(tmp_path):
    fill(tmp_path)
    seen = []

    def look(a):
        seen.append((a.shell.active_manager.active_panel.path, type(window(a)).__name__))

    usage_run(tmp_path, KeyEvent("g", alt=True), lambda a: None, look)
    assert seen[0][0] == tmp_path / "big"
    assert seen[0][1] != "UsageWindow"


def test_enter_on_a_file_puts_the_panel_on_it_and_the_window_stays(tmp_path):
    fill(tmp_path)
    seen = []

    def look(a):
        panel = a.shell.active_manager.active_panel
        seen.append((panel.path, panel.selected.name if panel.selected else None, type(window(a)).__name__))

    usage_run(tmp_path, KeyEvent("enter"), KeyEvent("down"), KeyEvent("down"), KeyEvent("enter"),
              Until(lambda a: a.shell.active_manager.active_panel.path == tmp_path / "big"), lambda a: None, look)
    assert seen == [(tmp_path / "big", "file", "UsageWindow")]


def test_closing_mid_read_stops_the_walk(tmp_path, monkeypatch):
    import threading

    from test_nav import navigator

    fill(tmp_path)
    jobs = []
    release = threading.Event()

    def slow(location, job=None, **kwargs):
        jobs.append(job)
        release.wait(2)
        return None if job.stopped else dirusage.UsageNode("x", is_dir=True)

    monkeypatch.setattr(dirusage, "scan", slow)
    app = navigator(tmp_path, size=(100, 30))

    def open_it(a):
        from navigator.widgets.shell.commands import OpenUsageWindow

        a.spawn(a.run_command(OpenUsageWindow))

    seen = []
    run_app(app, [open_it, Until(lambda a: bool(jobs)),
                  lambda a: seen.append(window(a).status.text.startswith("Reading")),
                  KeyEvent("escape"), lambda a: None, lambda a: release.set()])
    assert seen == [True]
    assert jobs[0].stopped
