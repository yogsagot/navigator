"""``UseFile``'s loop side (``navigator/widgets/drives/use_file.py``): a copy
fetched from another drive, put back -- and a window whose copy did not go
back stays unsaved, so closing asks before the copy is deleted."""

from __future__ import annotations

import asyncio
import errno

import pytest

from conftest import FakeTerminal, IDLE, Until, run_app
from navkit.events import KeyEvent

from navigator.lib.drives import mount, unmount, usefile
from navigator.lib.drives.memory import MemoryDrive
from navigator.lib.system.job import Job


class Counting(Job):
    position = total = 0


class Asked:
    """``Dialog`` in ``use_file``: each question recorded, answered from a script."""

    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.answers: list = []
        outer = self

        class FakeDialog:
            def __init__(self, *, title="", prompt="", buttons="ok", **_kw) -> None:
                self.prompt = prompt
                self.buttons = buttons

            async def execute(self, app):
                outer.prompts.append(self.prompt)
                return outer.answers.pop(0) if outer.answers else None

        self.dialog = FakeDialog


@pytest.fixture
def asked(monkeypatch):
    questions = Asked()
    monkeypatch.setattr("navigator.widgets.drives.use_file.Dialog", questions.dialog)
    return questions


@pytest.fixture
def desk(tmp_path, monkeypatch):
    from navigator.__main__ import Navigator
    from navigator.settings import SETTINGS

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr(SETTINGS.confirmations, "save", False)
    drive = mount(MemoryDrive("use"))
    drive.make("/files/one.txt", "first")
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))
    yield app, drive
    unmount(drive.site)


def policy(monkeypatch, value):
    from navigator.settings import SETTINGS

    monkeypatch.setattr(SETTINGS.remote, "upload_changed", value)


def failing(drive, monkeypatch):
    """*drive*'s writes refused, as a full disk there would; returns a switch back."""
    def refuse(*_a, **_k):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(drive, "open_write", refuse)
    return lambda: monkeypatch.delattr(drive, "open_write")


def fetched(drive, text=None):
    use = usefile.fetch([drive.location("/files/one.txt")], Counting())
    if text is not None:
        use.copies[0].local.write_text(text)
    return use


def put_back_result(app, use, **kw):
    """``put_back`` run on the live loop; its answer in the returned dict."""
    from navigator.widgets.drives.use_file import put_back

    out: dict = {}

    def start(a):
        async def go():
            out["sent"] = await put_back(a, use, **kw)
        asyncio.ensure_future(go())

    return out, [start, Until(lambda a: "sent" in out, timeout=5)]


# -- put_back ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("setting, answers, sent, there", [
    ("always", [], True, b"changed"),
    ("ask", [True], True, b"changed"),
    ("ask", [False], False, b"first"),
    ("never", [], False, b"first"),
])
def test_put_back_follows_upload_changed(desk, asked, monkeypatch, setting, answers, sent, there):
    app, drive = desk
    policy(monkeypatch, setting)
    asked.answers = list(answers)
    use = fetched(drive, "changed")
    try:
        out, steps = put_back_result(app, use)
        run_app(app, steps)
    finally:
        usefile.discard(use)
    assert out["sent"] is sent
    assert drive.read("/files/one.txt") == there
    assert len(asked.prompts) == (1 if setting == "ask" else 0)


def test_nothing_changed_counts_as_in_step(desk, asked):
    app, drive = desk
    use = fetched(drive)
    try:
        out, steps = put_back_result(app, use, ask=False)
        run_app(app, steps)
    finally:
        usefile.discard(use)
    assert out["sent"] is True and asked.prompts == []


@pytest.mark.parametrize("overwrite", [False, True])
def test_a_file_changed_there_since_the_fetch_is_asked_about(desk, asked, overwrite):
    app, drive = desk
    use = fetched(drive, "mine")
    drive.make("/files/one.txt", "theirs, longer")
    asked.answers = [overwrite]
    try:
        out, steps = put_back_result(app, use, ask=False)
        run_app(app, steps)
    finally:
        usefile.discard(use)
    assert out["sent"] is overwrite
    assert "changed there since it was fetched" in asked.prompts[0]
    assert drive.read("/files/one.txt") == (b"mine" if overwrite else b"theirs, longer")


def test_a_failed_upload_is_said_and_is_not_sent(desk, asked, monkeypatch):
    app, drive = desk
    failing(drive, monkeypatch)
    use = fetched(drive, "changed")
    try:
        out, steps = put_back_result(app, use, ask=False)
        run_app(app, steps)
        # Still changed: a later try sends it.
        assert usefile.changed(use) == use.copies
    finally:
        usefile.discard(use)
    assert out["sent"] is False
    assert asked.prompts and "No space left on device" in asked.prompts[0]
    assert drive.read("/files/one.txt") == b"first"


# -- the editor ---------------------------------------------------------------------------------------


def editor(app):
    from navigator.widgets.editor.edit_window import EditWindow

    return next((w for w in app.shell.desktop.windows() if isinstance(w, EditWindow)), None)


def on_one(drive):
    def action(app):
        panel = app.manager.left
        if panel.location != drive.location("/files"):
            panel.location = drive.location("/files")
            return
        panel.cursor = [entry.name for entry in panel.items].index("one.txt")
    return action


def edit_and_save(drive):
    return [
        on_one(drive), Until(lambda a: len(a.manager.left.items) == 2),
        on_one(drive),
        KeyEvent("f4"), Until(lambda a: editor(a) is not None, timeout=5),
        KeyEvent("x", char="x"), KeyEvent("f2"), IDLE,
    ]


def test_a_failed_upload_leaves_the_editor_unsaved_and_closing_asks(desk, asked, monkeypatch):
    app, drive = desk
    recover = failing(drive, monkeypatch)
    seen: dict = {}

    def failed(a):
        window = editor(a)
        seen.update(unsent=window.unsent, modified=window.editor.modified, must_ask=window.must_ask(),
                    title=window.title, local=window.editor.path)
        asked.prompts.clear()
        recover()
        asked.answers = [True]  # Upload it now? -- Yes
        window.request_close()

    run_app(app, [
        *edit_and_save(drive), failed,
        Until(lambda a: editor(a) is None, timeout=5),
        Until(lambda a: not seen["local"].parent.exists(), timeout=5),
    ])
    assert seen["unsent"] and not seen["modified"] and seen["must_ask"]
    assert seen["title"].startswith(("☼ ", "* "))
    assert "is saved here but not on" in asked.prompts[0]
    assert drive.read("/files/one.txt") == b"xfirst"


def test_no_to_the_upload_question_closes_and_lets_the_copy_go(desk, asked, monkeypatch):
    app, drive = desk
    failing(drive, monkeypatch)
    seen: dict = {}

    def close(a):
        seen["local"] = editor(a).editor.path
        asked.answers = [False]
        editor(a).request_close()

    run_app(app, [
        *edit_and_save(drive), close,
        Until(lambda a: editor(a) is None, timeout=5),
        Until(lambda a: not seen["local"].parent.exists(), timeout=5),
    ])
    assert drive.read("/files/one.txt") == b"first"


def test_cancel_keeps_the_editor_and_its_copy(desk, asked, monkeypatch):
    app, drive = desk
    failing(drive, monkeypatch)
    seen: dict = {}

    def close(a):
        asked.answers = [None]
        editor(a).request_close()

    run_app(app, [
        *edit_and_save(drive), close, IDLE,
        lambda a: seen.update(open=editor(a) is not None, local=editor(a).editor.path.exists()),
    ])
    assert seen == {"open": True, "local": True}


def test_f2_again_once_the_drive_is_back_sends_it(desk, asked, monkeypatch):
    app, drive = desk
    recover = failing(drive, monkeypatch)
    seen: dict = {}
    run_app(app, [
        *edit_and_save(drive),
        lambda a: (seen.update(first=editor(a).unsent), recover()),
        KeyEvent("f2"), IDLE,
        lambda a: seen.update(after=editor(a).unsent, must_ask=editor(a).must_ask()),
    ])
    assert seen == {"first": True, "after": False, "must_ask": False}
    assert drive.read("/files/one.txt") == b"xfirst"


def held_upload(monkeypatch):
    """``usefile.upload`` held until the returned *closed* is set; *started*
    is set once an upload is waiting there."""
    import threading

    started, closed = threading.Event(), threading.Event()
    upload = usefile.upload

    def slow(changed, job):
        started.set()
        closed.wait(5)
        return upload(changed, job)

    monkeypatch.setattr(usefile, "upload", slow)
    return started, closed


def test_an_editor_closed_while_its_f2_uploads_lets_the_copy_go_after(desk, asked, monkeypatch):
    # The upload's box shows only after a second: a window closed inside it
    # used to delete the copy the upload was about to read.
    app, drive = desk
    started, closed = held_upload(monkeypatch)
    seen: dict = {}

    def close(a):
        window = editor(a)
        seen["local"] = window.editor.path
        window.close()
        seen["kept"] = seen["local"].exists()
        closed.set()

    run_app(app, [
        on_one(drive), Until(lambda a: len(a.manager.left.items) == 2),
        on_one(drive),
        KeyEvent("f4"), Until(lambda a: editor(a) is not None, timeout=5),
        KeyEvent("x", char="x"), KeyEvent("f2"),
        Until(lambda a: started.is_set(), timeout=5),
        close,
        Until(lambda a: not seen["local"].parent.exists(), timeout=5),
    ])
    assert seen["kept"]
    assert asked.prompts == []
    assert drive.read("/files/one.txt") == b"xfirst"


# -- the viewers --------------------------------------------------------------------------------------


def test_bytes_stored_in_hex_whose_upload_failed_keep_the_viewer_asking(desk, asked, monkeypatch):
    from navigator.lib.config.file_history import open_viewer

    app, drive = desk
    use = fetched(drive)
    failing(drive, monkeypatch)
    seen: dict = {}

    def open_copy(a):
        async def go():
            window = await open_viewer(a.shell.desktop, use.copies[0].local, "hex")
            window.use_set = use
            seen["window"] = window
        asyncio.ensure_future(go())

    run_app(app, [
        open_copy, Until(lambda a: "window" in seen, timeout=5),
        KeyEvent("4", "4"), KeyEvent("a", "a"), KeyEvent("f2", shift=True), IDLE,
        lambda a: seen.update(unsent=seen["window"].unsent, edited=seen["window"].viewer.edited,
                              must_ask=seen["window"].must_ask()),
    ])
    assert seen["unsent"] and not seen["edited"] and seen["must_ask"]
    assert use.copies[0].local.read_bytes()[:1] == b"J"
    assert drive.read("/files/one.txt") == b"first"


def test_a_viewer_closed_while_its_stored_bytes_upload_lets_the_copy_go_after(desk, asked, monkeypatch):
    from navigator.lib.config.file_history import open_viewer

    app, drive = desk
    use = fetched(drive)
    started, closed = held_upload(monkeypatch)
    seen: dict = {}

    def open_copy(a):
        async def go():
            window = await open_viewer(a.shell.desktop, use.copies[0].local, "hex")
            window.use_set = use
            seen["window"] = window
        asyncio.ensure_future(go())

    def close(a):
        seen["window"].close()
        seen["kept"] = use.directory.exists()
        closed.set()

    run_app(app, [
        open_copy, Until(lambda a: "window" in seen, timeout=5),
        KeyEvent("4", "4"), KeyEvent("a", "a"), KeyEvent("f2", shift=True),
        Until(lambda a: started.is_set(), timeout=5),
        close,
        Until(lambda a: not use.directory.exists(), timeout=5),
    ])
    assert seen["kept"]
    assert asked.prompts == []
    assert drive.read("/files/one.txt") == b"Jirst"


def test_a_database_window_with_an_upload_owed_asks_before_closing(desk, asked):
    from navigator.widgets.viewer.db_window import DBWindow

    app, drive = desk
    use = fetched(drive, "changed")
    try:
        window = DBWindow()
        window.use_set = use
        assert not window.must_ask()
        window.unsent = True
        assert window.must_ask()
        asked.answers = [False]
        assert asyncio.run(window.ask_to_close()) is True
        asked.answers = [None]
        assert asyncio.run(window.ask_to_close()) is False
    finally:
        usefile.discard(use)
