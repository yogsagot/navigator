"""*As root*: ``navigator/lib/system/elevate.py``, the root helper and ``RootDrive``.

Root is never asked for.  ``ELEVATION.command`` starts the helper unprivileged,
so the protocol, the drive and the workers' retries are exercised as the user;
a refusal is set up by a directory without write permission, put right just
before the test answers *As root*, so the retry through the helper can work.
A small script stands in for sudo's password exchange.
"""

from __future__ import annotations

import errno
import os
import sys
import textwrap
from pathlib import Path

import pytest

from navigator.lib.drives.location import Location
from navigator.lib.drives.root import ROOT_DRIVE
from navigator.lib.file_ops import fileerase
from navigator.lib.file_ops.filecopy import AS_ROOT, ASK, CopyJob, CopyRequest, Failure, run
from navigator.lib.system import elevate
from navigator.lib.system.elevate import ELEVATION, MARKER, READY_STATE, Asked, Refused
from navigator.settings import SETTINGS

IS_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0
BOOT = [sys.executable, "-I", "-c", elevate._BOOT]


@pytest.fixture
def helper():
    """The helper, run as the user, closed afterwards -- and no panel left
    holding it from a test whose app ended with a panel at ``root:``."""
    from navigator.lib.drives import root, unmount

    ELEVATION.command = list(BOOT)
    yield ELEVATION
    root._HOLDERS.clear()
    unmount(root.ROOT_SITE)
    ELEVATION.close()
    ELEVATION.command = None


@pytest.fixture
def started(helper):
    assert helper.begin() == READY_STATE
    return helper


# -- starting ---------------------------------------------------------------------


def test_the_helper_starts_and_answers(started):
    assert started.running
    assert started.begin() == READY_STATE  # already running


def test_an_unknown_request_is_refused(started):
    with pytest.raises(OSError) as raised:
        started.call("eval", source="1")
    assert raised.value.errno == errno.EINVAL
    assert started.running


def test_a_helper_that_ends_at_once_is_a_refusal(helper):
    helper.command = [sys.executable, "-c", "import sys; sys.stderr.write('not allowed\\n'); sys.exit(1)"]
    state = helper.begin()
    assert isinstance(state, Refused) and state.reason == "not allowed"
    assert not helper.running


def test_a_step_without_the_helper_is_refused(helper):
    with pytest.raises(OSError) as raised:
        helper.call("stat", path="/")
    assert raised.value.errno == errno.EACCES


@pytest.fixture
def fake_sudo(tmp_path, helper):
    """A sudo that asks on stderr, as ``sudo -S -p MARKER`` does, and
    starts the helper once told ``secret``."""
    script = tmp_path / "sudo.py"
    script.write_text(textwrap.dedent(f"""
        import os, sys
        for attempt in range(3):
            if attempt:
                sys.stderr.write("Sorry, try again.\\n")
            sys.stderr.write({MARKER!r})
            sys.stderr.flush()
            line = sys.stdin.readline()
            if not line:
                sys.exit(1)
            if line.strip() == "secret":
                os.execv(sys.executable, {BOOT!r})
        sys.stderr.write("3 incorrect password attempts\\n")
        sys.exit(1)
    """))
    helper.command = [sys.executable, str(script)]
    return helper


def test_a_password_is_asked_for_and_a_wrong_one_said(fake_sudo):
    state = fake_sudo.begin()
    assert isinstance(state, Asked) and not state.wrong
    state = fake_sudo.answer("guess")
    assert isinstance(state, Asked) and state.wrong
    assert fake_sudo.answer("secret") == READY_STATE
    assert fake_sudo.call("exists", path="/")


def test_giving_up_on_the_password_closes_it(fake_sudo):
    assert isinstance(fake_sudo.begin(), Asked)
    state = fake_sudo.answer(None)
    assert isinstance(state, Refused) and state.reason == ""
    assert not fake_sudo.running


def test_too_many_wrong_passwords_are_a_refusal(fake_sudo):
    fake_sudo.begin()
    fake_sudo.answer("a")
    fake_sudo.answer("b")
    state = fake_sudo.answer("c")
    assert isinstance(state, Refused) and "incorrect" in state.reason


def test_off_offers_nothing(monkeypatch):
    monkeypatch.setattr(SETTINGS.system, "elevate", "off")
    assert ELEVATION.tool() is None
    assert not ELEVATION.available()


def test_release_closes_it_with_no_timeout(started, monkeypatch):
    monkeypatch.setattr(SETTINGS.system, "root_timeout", 5)
    started.release()
    assert started.running
    monkeypatch.setattr(SETTINGS.system, "root_timeout", 0)
    started.release()
    assert not started.running


# -- the drive --------------------------------------------------------------------


def test_the_drive_reads_writes_and_lists(started, tmp_path):
    big = os.urandom(3 << 20)  # more than one request's worth
    where = Location.of(tmp_path / "f.bin")
    with ROOT_DRIVE.open_write(where, mode=0o640) as writer:
        writer.write(big)
    with ROOT_DRIVE.open_read(where) as reader:
        assert reader.read() == big
    assert ROOT_DRIVE.stat(where).st_size == len(big)
    assert ROOT_DRIVE.stat(where).st_mtime == os.stat(tmp_path / "f.bin").st_mtime
    ROOT_DRIVE.mkdir(Location.of(tmp_path / "d"))
    assert sorted(ROOT_DRIVE.names(Location.of(tmp_path))) == ["d", "f.bin"]
    assert dict(ROOT_DRIVE.children(Location.of(tmp_path)))["d"].st_mode & 0o040000
    ROOT_DRIVE.rename(where, Location.of(tmp_path / "g.bin"))
    ROOT_DRIVE.unlink(Location.of(tmp_path / "g.bin"))
    ROOT_DRIVE.rmdir(Location.of(tmp_path / "d"))
    assert list(tmp_path.iterdir()) == []


def test_the_drive_raises_what_the_helper_met(started, tmp_path):
    with pytest.raises(FileNotFoundError) as raised:
        ROOT_DRIVE.stat(Location.of(tmp_path / "missing"))
    assert raised.value.filename == str(tmp_path / "missing")


def test_the_editor_saves_through_it(started, tmp_path):
    path = tmp_path / "text.txt"
    path.write_bytes(b"old\n")
    path.chmod(0o604)
    ROOT_DRIVE.write_file(path, iter([b"new ", b"text\n"]), backup=True)
    assert path.read_bytes() == b"new text\n"
    assert (tmp_path / "text.txt.bak").read_bytes() == b"old\n"
    assert path.stat().st_mode & 0o777 == 0o604


def test_the_editors_own_lock_does_not_refuse_its_save(started, tmp_path, monkeypatch):
    from navigator.lib.editor import lock

    path = tmp_path / "held.txt"
    path.write_text("x")
    key = lock.take(path)
    try:
        ROOT_DRIVE.write_file(path, [b"y"])
    finally:
        lock.release(key)
    assert path.read_text() == "y"


# -- the workers ------------------------------------------------------------------


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_a_copy_refused_goes_on_as_root(helper, tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.txt").write_text("alpha")
    (tmp_path / "src" / "b.txt").write_text("beta")
    locked = tmp_path / "locked"
    locked.mkdir(mode=0o500)
    asked: list = []
    calls: list = []
    real_call = ELEVATION.call_data

    def counted(op, *args, **kwargs):
        calls.append(op)
        return real_call(op, *args, **kwargs)

    def asker(question):
        asked.append(question)
        assert isinstance(question, Failure) and question.elevate
        locked.chmod(0o700)  # what root could have done anyway
        assert ELEVATION.begin() == READY_STATE
        return AS_ROOT

    ELEVATION.call_data = counted  # type: ignore[method-assign]
    try:
        job = CopyJob(asker=asker)
        sources = [tmp_path / "src" / "a.txt", tmp_path / "src" / "b.txt"]
        done = run(CopyRequest(sources, str(locked), ASK, 0), job, tmp_path)
    finally:
        del ELEVATION.call_data
    assert done == sources and len(asked) == 1  # asked once, for both
    assert (locked / "a.txt").read_text() == "alpha" and (locked / "b.txt").read_text() == "beta"
    assert "open_write" in calls


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_a_refusal_as_root_is_not_offered_again(helper, tmp_path):
    (tmp_path / "a.txt").write_text("alpha")
    locked = tmp_path / "locked"
    locked.mkdir(mode=0o500)
    asked: list = []

    def asker(question):
        asked.append(question)
        if len(asked) == 1:
            assert ELEVATION.begin() == READY_STATE
            return AS_ROOT
        return True  # skip

    try:
        done = run(CopyRequest([tmp_path / "a.txt"], str(locked), ASK, 0), CopyJob(asker=asker), tmp_path)
    finally:
        locked.chmod(0o700)
    assert done == [] and [q.elevate for q in asked] == [True, False]


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_an_erase_refused_goes_on_as_root(helper, tmp_path):
    box = tmp_path / "box"
    box.mkdir()
    (box / "a.txt").write_text("a")
    box.chmod(0o500)
    asked: list = []

    def asker(question):
        asked.append(question)
        if isinstance(question, fileerase.ReadOnly):
            return fileerase.YES
        assert isinstance(question, Failure) and question.elevate
        box.chmod(0o700)
        assert ELEVATION.begin() == READY_STATE
        return AS_ROOT

    done = fileerase.run(fileerase.EraseRequest([box], recursive=True), fileerase.EraseJob(asker=asker))
    assert done == [box] and not box.exists()
    assert sum(isinstance(q, Failure) for q in asked) == 1


def test_a_refusal_off_the_disk_is_not_offered(tmp_path):
    from navigator.lib.file_ops.filecopy import Elevated

    worker = Elevated()
    refusal = OSError(errno.EACCES, "Permission denied")
    assert worker._offer(Location.of(tmp_path), refusal)
    assert not worker._offer(Location.of(tmp_path), OSError(errno.ENOSPC, "No space"))
    worker.elevated = True
    assert not worker._offer(Location.of(tmp_path), refusal)


def test_the_helper_ops_are_a_closed_list():
    from navigator.lib.system.roothelper import OPS

    assert "stat" in OPS and "write_text" in OPS
    assert not any(name.startswith("_") for name in OPS)
    assert Path(elevate._ROOT, "navigator", "lib", "system", "roothelper.py").is_file()


# -- the boxes --------------------------------------------------------------------


@pytest.fixture
def quiet_console(monkeypatch):
    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)


def test_as_root_asks_the_password_and_answers_as_root(fake_sudo, tmp_path, quiet_console):
    from conftest import FakeTerminal, Until, run_app
    from navigator.__main__ import Navigator
    from navigator.widgets.drives.password_dialog import PasswordDialog
    from navigator.widgets.file_ops.as_root import ask_skip

    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    answers: list = []
    prompts: list = []

    async def ask(a):
        answers.append(await ask_skip(a, "Permission denied", elevate=True))

    def type_password(text):
        def act(a):
            prompts.append(a.modal.prompt)
            a.modal.entry.value = text
            a.spawn(a.modal.ok.press())
        return act

    run_app(app, [
        lambda a: a.spawn(ask(a)),
        Until(lambda a: a.modal is not None and a.modal.no.visible),
        lambda a: a.spawn(a.modal.no.press()),  # As root
        Until(lambda a: isinstance(a.modal, PasswordDialog), timeout=10),
        type_password("guess"),
        Until(lambda a: isinstance(a.modal, PasswordDialog) and len(prompts) == 1
              and a.modal.prompt != prompts[0], timeout=10),
        type_password("secret"),
        Until(lambda a: answers, timeout=10),
    ])
    assert answers == [AS_ROOT]
    assert "password" in prompts[0] and prompts[1] == "Wrong password. Try again:"
    assert not ELEVATION.running  # closed as Navigator stopped


def test_without_a_way_to_root_only_skip_and_cancel(tmp_path, quiet_console, monkeypatch):
    from conftest import FakeTerminal, Until, run_app
    from navigator.__main__ import Navigator
    from navigator.widgets.file_ops.as_root import ask_skip

    monkeypatch.setattr(SETTINGS.system, "elevate", "off")
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    answers: list = []
    seen: list = []

    async def ask(a):
        answers.append(await ask_skip(a, "Permission denied", elevate=True))

    def skip(a):
        seen.append(a.modal.no.visible)
        a.spawn(a.modal.ok.press())

    run_app(app, [
        lambda a: a.spawn(ask(a)),
        Until(lambda a: a.modal is not None),
        skip,
        Until(lambda a: answers),
    ])
    assert seen == [False] and answers == [True]


# -- attributes, mkdir, links -----------------------------------------------------


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_attributes_refused_go_on_as_root(helper, tmp_path):
    from navigator.lib.file_ops import fileattr

    box = tmp_path / "box"
    box.mkdir()
    (box / "a.txt").write_text("a")
    (box / "a.txt").chmod(0o600)
    box.chmod(0)  # nothing under it can be read
    asked: list = []

    def asker(question):
        asked.append(question)
        assert isinstance(question, Failure) and question.elevate
        box.chmod(0o700)
        assert ELEVATION.begin() == READY_STATE
        return AS_ROOT

    request = fileattr.AttrRequest(sources=[box], set_bits=0o044, clear_bits=0, recurse=fileattr.ALL)
    try:
        done = fileattr.run(request, fileattr.AttrJob(asker=asker))
    finally:
        box.chmod(0o755)
    assert done == [box] and len(asked) == 1
    assert (box / "a.txt").stat().st_mode & 0o777 == 0o644


def test_apply_one_as_root_makes_the_same_calls(started, tmp_path):
    from navigator.lib.file_ops import fileattr

    path = tmp_path / "f"
    path.write_text("x")
    path.chmod(0o600)
    request = fileattr.AttrRequest(sources=[path], set_bits=0o004, clear_bits=0o200, mtime=1_000_000_000)
    fileattr.apply_one(path, request, as_root=True)
    st = path.stat()
    assert st.st_mode & 0o777 == 0o404 and st.st_mtime == 1_000_000_000


def manager_of(app):
    return app.shell.active_manager


def entry_named(panel, name):
    return next(entry for entry in panel.items if entry.name == name)


def press_as_root(locked):
    """The error box's *As root*, the refusal put right just before."""
    def act(a):
        locked.chmod(0o700)
        a.spawn(a.modal.ok.press())
    return act


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_mkdir_refused_is_made_as_root(helper, tmp_path, quiet_console):
    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog

    locked = tmp_path / "locked"
    locked.mkdir(mode=0o500)
    app = Navigator(locked, locked, terminal=FakeTerminal(80, 24))
    seen: list = []
    try:
        run_app(app, [
            KeyEvent("f7"), Until(lambda a: isinstance(a.modal, MkdirDialog)),
            *[KeyEvent(c, c) for c in "new"], KeyEvent("enter"),
            Until(lambda a: a.modal is not None and not isinstance(a.modal, MkdirDialog)),
            lambda a: seen.append((a.modal.ok.text, a.modal.prompt)),
            press_as_root(locked),
            Until(lambda a: (locked / "new").is_dir(), timeout=10),
        ])
    finally:
        locked.chmod(0o700)
    assert seen[0][0].replace("~", "") == "As root" and "new" in seen[0][1]


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_links_refused_are_made_as_root(helper, tmp_path, quiet_console):
    from conftest import FakeTerminal, Until, run_app
    from navigator.__main__ import Navigator

    here = tmp_path / "here"
    here.mkdir()
    (here / "a.txt").write_text("a")
    (here / "b.txt").write_text("b")
    locked = tmp_path / "locked"
    locked.mkdir(mode=0o500)
    app = Navigator(here, locked, terminal=FakeTerminal(80, 24))
    boxes: list = []

    def link(a):
        manager = manager_of(a)
        panel = manager.active_panel
        entries = [entry_named(panel, "a.txt"), entry_named(panel, "b.txt")]
        a.spawn(manager.link_entries(panel, entries, locked, ask=False))

    def as_root(a):
        boxes.append(a.modal.no.text)
        locked.chmod(0o700)
        a.spawn(a.modal.no.press())

    try:
        run_app(app, [
            Until(lambda a: any(e.name == "a.txt" for e in manager_of(a).active_panel.items)),
            link,
            Until(lambda a: a.modal is not None),
            as_root,
            Until(lambda a: (locked / "b.txt").is_symlink(), timeout=10),
        ])
    finally:
        locked.chmod(0o700)
    assert boxes == ["As ~r~oot"]  # asked once, for both
    assert os.readlink(locked / "a.txt") == str(here / "a.txt")


# -- renames and the editor -------------------------------------------------------


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_a_multi_rename_refused_goes_on_as_root(helper, tmp_path):
    from navigator.lib.drives import drive_of
    from navigator.lib.file_ops import multirename

    locked = tmp_path / "locked"
    locked.mkdir()
    for name in ("a", "b", "c"):
        (locked / name).write_text(name)
    locked.chmod(0o500)
    asked: list = []

    def asker(question):
        asked.append(question)
        assert isinstance(question, Failure) and question.elevate
        locked.chmod(0o700)
        assert ELEVATION.begin() == READY_STATE
        return AS_ROOT

    here = Location.of(locked)
    # A swap through a temporary name, and a plain rename.
    pairs = [(here, "a", "b"), (here, "b", "a"), (here, "c", "d")]
    job = multirename.RenameJob(asker=asker)
    try:
        done = multirename.run(pairs, job, drive_of)
    finally:
        locked.chmod(0o700)
    assert len(asked) == 1 and job.elevated
    assert sorted(new for _, _, new in done) == ["a", "b", "d"]
    assert (locked / "a").read_text() == "b" and (locked / "b").read_text() == "a"
    assert (locked / "d").read_text() == "c"


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_a_multi_rename_skipped_is_not_renamed(helper, tmp_path):
    from navigator.lib.drives import drive_of
    from navigator.lib.file_ops import multirename

    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "a").write_text("a")
    locked.chmod(0o500)
    try:
        done = multirename.run([(Location.of(locked), "a", "z")], multirename.RenameJob(asker=lambda q: True),
                               drive_of)
    finally:
        locked.chmod(0o700)
    assert done == [] and (locked / "a").exists()


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_a_quick_rename_refused_is_done_as_root(helper, tmp_path, quiet_console):
    from conftest import FakeTerminal, Until, run_app
    from navigator.__main__ import Navigator

    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "old.txt").write_text("x")
    locked.chmod(0o500)
    app = Navigator(locked, locked, terminal=FakeTerminal(80, 24))
    seen: list = []

    def rename(a):
        manager = manager_of(a)
        panel = manager.active_panel
        a.spawn(manager._rename_entry(panel, entry_named(panel, "old.txt"), "new.txt"))

    def as_root(a):
        seen.append(a.modal.ok.text)
        locked.chmod(0o700)
        a.spawn(a.modal.ok.press())

    try:
        run_app(app, [
            Until(lambda a: any(e.name == "old.txt" for e in manager_of(a).active_panel.items)),
            rename,
            Until(lambda a: a.modal is not None),
            as_root,
            Until(lambda a: (locked / "new.txt").exists(), timeout=10),
        ])
    finally:
        locked.chmod(0o700)
    assert seen == ["As ~r~oot"] and not (locked / "old.txt").exists()


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_f2_refused_saves_as_root(helper, tmp_path, quiet_console, monkeypatch):
    from conftest import IDLE, FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.widgets.editor.edit_window import EditWindow

    monkeypatch.setattr(SETTINGS.confirmations, "save", False)
    locked = tmp_path / "locked"
    locked.mkdir()
    path = locked / "text.txt"
    path.write_bytes(b"old\n")
    path.chmod(0o444)
    locked.chmod(0o500)
    app = Navigator(locked, locked, terminal=FakeTerminal(80, 24))
    seen: list = []

    def as_root(a):
        seen.append(a.modal.ok.text)
        locked.chmod(0o700)
        path.chmod(0o644)
        a.spawn(a.modal.ok.press())

    try:
        run_app(app, [
            Until(lambda a: any(e.name == "text.txt" for e in manager_of(a).active_panel.items)),
            KeyEvent("end"), KeyEvent("f4"), IDLE,
            KeyEvent("x", "x"), lambda a: None, KeyEvent("f2"),
            Until(lambda a: a.modal is not None and not isinstance(a.modal, EditWindow), timeout=5),
            as_root,
            Until(lambda a: path.read_bytes() == b"xold\n", timeout=10),
            IDLE,
        ])
    finally:
        locked.chmod(0o700)
    assert seen == ["As ~r~oot"]


# -- F3, ^K R and ^K W ------------------------------------------------------------


def test_a_held_file_keeps_the_helper_open(started, monkeypatch):
    monkeypatch.setattr(SETTINGS.system, "root_timeout", 0)
    started.hold()
    started.release()
    assert started.running
    started.unhold()
    started.release()
    assert not started.running


def test_f3s_source_reads_chunks_through_the_helper(started, tmp_path, monkeypatch):
    from navigator.lib.viewer import CHUNK, ChunkedSource

    monkeypatch.setattr(SETTINGS.system, "root_timeout", 0)
    data = os.urandom(CHUNK * 2 + 17)
    (tmp_path / "f.bin").write_bytes(data)
    origin = Location.of(tmp_path / "f.bin")
    source = ChunkedSource(origin, len(data), ROOT_DRIVE.open_random(origin))
    source.drive = ROOT_DRIVE
    assert source.read_blocking(CHUNK - 3, 10) == data[CHUNK - 3:CHUNK + 7]
    with source.stream() as stream:
        assert stream.read() == data
    source.close()
    assert not started.running  # let go with the window


def test_read_text_as_root_reads_through_the_helper(started, tmp_path):
    from navigator.lib.editor.document import read_text

    (tmp_path / "t.txt").write_bytes(b"one\r\ntwo\n")
    calls: list = []
    real = ELEVATION.call_data

    def counted(op, *args, **kwargs):
        calls.append(op)
        return real(op, *args, **kwargs)

    ELEVATION.call_data = counted  # type: ignore[method-assign]
    try:
        assert read_text(tmp_path / "t.txt", as_root=True) == "one\r\ntwo\n"
    finally:
        del ELEVATION.call_data
    assert "open_read" in calls and "stat" in calls


@pytest.fixture
def editing(tmp_path, quiet_console, monkeypatch):
    """Navigator with an editor open on ``text.txt``, its window handed back."""
    from conftest import IDLE, FakeTerminal, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.widgets.editor.edit_window import EditWindow

    monkeypatch.setattr(SETTINGS.confirmations, "save", False)
    (tmp_path / "text.txt").write_bytes(b"line\n")
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))

    def window(a):
        found = a.shell.desktop.active_window
        return found if isinstance(found, EditWindow) else None

    opened = [KeyEvent("end"), KeyEvent("f4"), IDLE]
    return app, opened, window


def press_ok_after(fix):
    def act(a):
        fix()
        a.spawn(a.modal.ok.press())
    return act


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_ctrl_k_r_refused_reads_as_root(helper, tmp_path, editing):
    from conftest import Until, run_app

    app, opened, window = editing
    secret = tmp_path / "secret.txt"
    secret.write_text("hidden\n")
    secret.chmod(0)

    async def block_file(*_args):
        return secret

    def read(a):
        w = window(a)
        w._block_file = block_file
        a.spawn(w.read_block())

    try:
        run_app(app, [
            *opened, read,
            Until(lambda a: a.modal is not None and a.modal is not window(a), timeout=5),
            press_ok_after(lambda: secret.chmod(0o600)),
            Until(lambda a: "hidden" in "".join(window(a).editor.document.lines), timeout=10),
        ])
    finally:
        secret.chmod(0o600)


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_ctrl_k_w_refused_writes_as_root(helper, tmp_path, editing):
    from conftest import Until, run_app

    app, opened, window = editing
    locked = tmp_path / "locked"
    locked.mkdir(mode=0o500)
    target = locked / "block.txt"

    async def block_file(*_args):
        return target

    def write(a):
        w = window(a)
        w._block_file = block_file
        w.editor.block_file_text = lambda: "the block\n"
        a.spawn(w.write_block())

    try:
        run_app(app, [
            *opened, write,
            Until(lambda a: a.modal is not None and a.modal is not window(a), timeout=5),
            press_ok_after(lambda: locked.chmod(0o700)),
            Until(lambda a: target.exists() and target.read_text() == "the block\n", timeout=10),
        ])
    finally:
        locked.chmod(0o700)


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_f3_refused_views_as_root(helper, tmp_path, quiet_console, monkeypatch):
    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.lib.viewer import ChunkedSource
    from navigator.widgets.viewer.file_window import FileWindow

    monkeypatch.setattr(SETTINGS.system, "root_timeout", 0)
    secret = tmp_path / "secret.txt"
    secret.write_text("hidden text\n")
    secret.chmod(0)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen: dict = {}

    def viewer(a):
        found = a.shell.desktop.active_window
        return found if isinstance(found, FileWindow) else None

    def look(a):
        source = viewer(a).viewer.source
        seen.update(chunked=isinstance(source, ChunkedSource), title=viewer(a).title,
                    text=source.read_blocking(0, 64), running=ELEVATION.running)

    try:
        run_app(app, [
            Until(lambda a: any(e.name == "secret.txt" for e in manager_of(a).active_panel.items)),
            KeyEvent("end"), KeyEvent("f3"),
            Until(lambda a: a.modal is not None, timeout=5),
            press_ok_after(lambda: secret.chmod(0o600)),
            Until(lambda a: viewer(a) is not None, timeout=10),
            look,
        ])
    finally:
        secret.chmod(0o600)
    assert seen == {"chunked": True, "title": str(secret), "text": b"hidden text\n", "running": True}


# -- F4, As DataBase, quick view --------------------------------------------------


def put_cursor_on(name):
    def act(a):
        panel = manager_of(a).active_panel
        panel.cursor = [e.name for e in panel.items].index(name)
    return act


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_f4_refused_opens_as_root(helper, tmp_path, quiet_console, monkeypatch):
    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.widgets.editor.edit_window import EditWindow

    monkeypatch.setattr(SETTINGS.system, "root_timeout", 0)
    secret = tmp_path / "secret.txt"
    secret.write_text("hidden\n")
    secret.chmod(0)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))

    def editor(a):
        found = a.shell.desktop.active_window
        return found if isinstance(found, EditWindow) else None

    seen: dict = {}
    try:
        run_app(app, [
            Until(lambda a: any(e.name == "secret.txt" for e in manager_of(a).active_panel.items)),
            put_cursor_on("secret.txt"), KeyEvent("f4"),
            Until(lambda a: a.modal is not None, timeout=5),
            press_ok_after(lambda: secret.chmod(0o600)),
            Until(lambda a: editor(a) is not None and editor(a).editor.document is not None, timeout=10),
            lambda a: seen.update(lines=editor(a).editor.document.lines[:1], path=editor(a).editor.path,
                                  running=ELEVATION.running),
        ])
    finally:
        secret.chmod(0o600)
    assert seen == {"lines": ["hidden"], "path": secret, "running": False}  # read, and let go


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_as_database_refused_opens_a_copy_as_root(helper, tmp_path, quiet_console):
    from test_dbf import write_dbf

    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.widgets.viewer.db_window import DBWindow

    people = write_dbf(tmp_path / "people.dbf")
    people.chmod(0)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))
    seen: dict = {}

    def window(a):
        found = a.shell.desktop.active_window
        return found if isinstance(found, DBWindow) else None

    def look(a):
        w = window(a)
        seen.update(title=w.title, count=w.db.count, copy=w.db.path, memo=w.db.path.with_suffix(".dbt").exists(),
                    mode=w.db.path.stat().st_mode & 0o077)

    try:
        run_app(app, [
            Until(lambda a: any(e.name == "people.dbf" for e in manager_of(a).active_panel.items)),
            put_cursor_on("people.dbf"), KeyEvent("f3"),
            Until(lambda a: a.modal is not None, timeout=5),
            press_ok_after(lambda: people.chmod(0o600)),
            Until(lambda a: window(a) is not None, timeout=10),
            look,
        ])
    finally:
        people.chmod(0o600)
    assert seen["title"] == str(people) and seen["count"] == 3 and seen["memo"]
    assert seen["copy"] != people and seen["mode"] == 0  # private: the owner's alone


def test_a_copy_fetched_as_root_goes_back_keeping_owner_and_mode(started, tmp_path):
    from navigator.lib.drives import usefile
    from navigator.lib.editor.save import resolve  # noqa: F401 - the write is the editor's
    from navigator.lib.system.job import Job

    origin = tmp_path / "data.bin"
    origin.write_bytes(b"before")
    origin.chmod(0o640)
    use = usefile.fetch([Location.of(origin)], Job(), drive=ROOT_DRIVE)
    try:
        copy = use.copies[0]
        assert copy.drive is ROOT_DRIVE and copy.local.read_bytes() == b"before"
        assert copy.local.stat().st_mode & 0o077 == 0
        copy.local.write_bytes(b"after!")
        assert usefile.changed(use) == [copy] and usefile.conflicts([copy]) == []
        job = Job()
        usefile.upload([copy], job)
    finally:
        usefile.discard(use)
    assert origin.read_bytes() == b"after!" and origin.stat().st_mode & 0o777 == 0o640


def test_quick_view_shows_an_unreadable_file_only_while_root_is_open(helper, tmp_path, quiet_console,
                                                                     monkeypatch):
    from conftest import FakeTerminal, Until, run_app
    from navigator.__main__ import Navigator
    from navigator.lib.viewer import ChunkedSource
    from navigator.widgets.viewer.quick_viewer import QuickViewer

    secret = tmp_path / "secret.txt"
    secret.write_text("hidden\n")

    def refused(path):
        # The user's open refused; the (unprivileged) helper's goes ahead.
        raise PermissionError(errno.EACCES, "Permission denied", str(path))

    monkeypatch.setattr("navigator.widgets.viewer.quick_viewer.quick_viewer.ViewSource", refused)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    quick = QuickViewer()
    seen: dict = {}

    def show(a):
        a.root.add(quick)
        quick.show(secret)

    def open_root_and_show_again(a):
        seen["closed"] = quick.viewer.source is None
        assert ELEVATION.begin() == READY_STATE
        quick.show(None)
        quick.show(secret)

    def look(a):
        source = quick.viewer.source
        seen.update(chunked=isinstance(source, ChunkedSource), text=source.read_blocking(0, 64))
        quick.show(None)

    run_app(app, [
        show, Until(lambda a: quick._wanted == secret and quick.viewer.source is None, timeout=5),
        lambda a: None, lambda a: None,
        open_root_and_show_again,
        Until(lambda a: quick.viewer.source is not None, timeout=10),
        look,
    ])
    assert seen == {"closed": True, "chunked": True, "text": b"hidden\n"}


# -- UU encode/decode, Alt+L ------------------------------------------------------


@pytest.fixture
def uu_place(tmp_path, quiet_console, monkeypatch):
    monkeypatch.setattr(SETTINGS.uucode, "lines_per_section", 100000)  # one section
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "blob.bin").write_bytes(os.urandom(5000))
    return tmp_path


def modal_named(name):
    return lambda a: a.modal is not None and type(a.modal).__name__ == name


def error_box(a):
    return a.modal is not None and type(a.modal).__name__ == "Dialog"


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_uu_encode_into_a_refused_directory_goes_on_as_root(helper, uu_place):
    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator

    locked = uu_place / "b"
    locked.chmod(0o500)
    app = Navigator(uu_place / "a", locked, terminal=FakeTerminal(80, 25))
    seen: list = []

    def as_root(a):
        seen.append(a.modal.ok.text)
        locked.chmod(0o700)
        a.spawn(a.modal.ok.press())

    try:
        run_app(app, [
            Until(lambda a: any(e.name == "blob.bin" for e in manager_of(a).left.items)),
            put_cursor_on("blob.bin"), KeyEvent("f7", ctrl=True), Until(modal_named("UUEncodeDialog")),
            lambda a: setattr(a.modal.target, "value", str(locked) + "/"), KeyEvent("enter"),
            Until(error_box, timeout=10), as_root,
            Until(lambda a: (locked / "blob.uue").exists() and a.modal is None, timeout=10),
        ])
    finally:
        locked.chmod(0o700)
    assert seen == ["As ~r~oot"]
    assert "begin 644 blob.bin" in (locked / "blob.uue").read_text().splitlines()


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_uu_decode_of_an_unreadable_file_goes_on_as_root(helper, uu_place):
    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.lib.file_ops.uucode import EncodeRequest, encode
    from navigator.lib.system.job import Job

    here = uu_place / "a"
    data = (here / "blob.bin").read_bytes()
    encode(EncodeRequest(here / "blob.bin", "blob.uue", lines=100000), Job(), here)
    (here / "blob.bin").unlink()
    (here / "blob.uue").chmod(0)
    app = Navigator(here, uu_place / "b", terminal=FakeTerminal(80, 25))
    try:
        run_app(app, [
            Until(lambda a: any(e.name == "blob.uue" for e in manager_of(a).left.items)),
            put_cursor_on("blob.uue"), KeyEvent("f8", ctrl=True), Until(modal_named("UUDecodeDialog")),
            lambda a: setattr(a.modal.target, "value", str(uu_place / "b") + "/"), KeyEvent("enter"),
            Until(error_box, timeout=10),
            press_ok_after(lambda: (here / "blob.uue").chmod(0o600)),
            Until(lambda a: (uu_place / "b" / "blob.bin").exists() and a.modal is None, timeout=10),
        ])
    finally:
        (here / "blob.uue").chmod(0o600)
    assert (uu_place / "b" / "blob.bin").read_bytes() == data


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_a_list_file_refused_is_written_as_root(helper, uu_place):
    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator

    locked = uu_place / "b"
    locked.chmod(0o500)
    app = Navigator(uu_place / "a", locked, terminal=FakeTerminal(80, 25))
    target = locked / "files.lst"
    try:
        run_app(app, [
            Until(lambda a: any(e.name == "blob.bin" for e in manager_of(a).left.items)),
            put_cursor_on("blob.bin"), KeyEvent("insert"),
            KeyEvent("l", alt=True), Until(modal_named("MakeListDialog")),
            lambda a: setattr(a.modal.file_name, "value", str(target)), KeyEvent("enter"),
            Until(error_box, timeout=10),
            press_ok_after(lambda: locked.chmod(0o700)),
            Until(lambda a: target.exists(), timeout=10),
        ])
    finally:
        locked.chmod(0o700)
    assert target.read_text() == "blob.bin\n"


# -- archives on the disk ---------------------------------------------------------


def make_zip(path, members=(("one.txt", "1"),)):
    import zipfile

    with zipfile.ZipFile(path, "w") as zipped:
        for name, text in members:
            zipped.writestr(name, text)
    return path


def zip_names(path):
    import zipfile

    with zipfile.ZipFile(path) as zipped:
        return sorted(zipped.namelist())


@pytest.fixture
def archives_closed():
    from navigator.lib.drives import archive

    yield
    archive.close_all()


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_an_unreadable_archive_is_refused_not_taken_for_a_program(tmp_path, archives_closed):
    from navigator.lib.drives import archive

    zipped = make_zip(tmp_path / "a.zip")
    zipped.chmod(0)
    try:
        with pytest.raises(PermissionError):
            archive.open_archive(Location.of(zipped))
    finally:
        zipped.chmod(0o644)


def test_an_archive_opened_as_root_is_put_back_through_it(started, tmp_path, archives_closed, monkeypatch):
    from navigator.lib.drives import archive

    monkeypatch.setattr(SETTINGS.system, "root_timeout", 0)
    zipped = make_zip(tmp_path / "a.zip")
    zipped.chmod(0o640)
    outer = Location.of(zipped)
    drive = archive.open_archive(outer, as_root=True)
    assert drive.as_root and drive.local != zipped
    with drive.open_write(drive.at("/") / "two.txt") as writer:
        writer.write(b"2")
    drive.finish()
    assert zip_names(zipped) == ["one.txt", "two.txt"] and zipped.stat().st_mode & 0o777 == 0o640
    started.release()
    assert started.running  # held while the archive is open
    archive.close_all()
    assert not started.running


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_a_copy_into_an_archive_whose_rewrite_is_refused_goes_on_as_root(helper, tmp_path, archives_closed):
    from navigator.lib.drives import archive

    locked = tmp_path / "locked"
    locked.mkdir()
    zipped = make_zip(locked / "a.zip")
    zipped.chmod(0o644)
    (tmp_path / "new.txt").write_text("new")
    locked.chmod(0o500)  # the zip can be read, not rewritten beside itself
    asked: list = []

    def asker(question):
        asked.append(question)
        assert isinstance(question, Failure) and question.elevate
        locked.chmod(0o700)  # what root could have done anyway
        assert ELEVATION.begin() == READY_STATE
        return AS_ROOT

    target = f"{zipped}#/"
    try:
        done = run(CopyRequest([tmp_path / "new.txt"], target, ASK, 0), CopyJob(asker=asker), tmp_path)
    finally:
        locked.chmod(0o700)
    assert done == [tmp_path / "new.txt"] and len(asked) == 1
    assert zip_names(zipped) == ["new.txt", "one.txt"] and zipped.stat().st_mode & 0o777 == 0o644
    assert archive.find(Location.of(zipped)) is None or archive.find(Location.of(zipped)).as_root


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_enter_on_an_unreadable_archive_offers_as_root(helper, tmp_path, quiet_console, archives_closed):
    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator

    zipped = make_zip(tmp_path / "a.zip")
    zipped.chmod(0)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen: dict = {}
    try:
        run_app(app, [
            Until(lambda a: any(e.name == "a.zip" for e in manager_of(a).active_panel.items)),
            put_cursor_on("a.zip"), KeyEvent("enter"),
            Until(lambda a: a.modal is not None, timeout=5),
            lambda a: seen.update(button=a.modal.ok.text),
            press_ok_after(lambda: zipped.chmod(0o644)),
            Until(lambda a: manager_of(a).active_panel.location.outer is not None, timeout=10),
            Until(lambda a: any(e.name == "one.txt" for e in manager_of(a).active_panel.items), timeout=5),
        ])
    finally:
        zipped.chmod(0o644)
    assert seen == {"button": "As ~r~oot"}


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_attributes_in_an_archive_whose_rewrite_is_refused_go_on_as_root(helper, tmp_path, archives_closed):
    import zipfile

    from navigator.lib.drives import archive
    from navigator.lib.file_ops import fileattr

    locked = tmp_path / "locked"
    locked.mkdir()
    zipped = make_zip(locked / "a.zip")
    locked.chmod(0o500)
    asked: list = []

    def asker(question):
        asked.append(question)
        assert isinstance(question, Failure) and question.elevate
        locked.chmod(0o700)
        assert ELEVATION.begin() == READY_STATE
        return AS_ROOT

    member = archive.open_archive(Location.of(zipped)).at("/") / "one.txt"
    request = fileattr.AttrRequest(sources=[member], set_bits=0o751, clear_bits=0o7777 & ~0o751)
    try:
        done = fileattr.run(request, fileattr.AttrJob(asker=asker))
    finally:
        locked.chmod(0o700)
    assert done == [member] and len(asked) == 1
    with zipfile.ZipFile(zipped) as reopened:
        assert (reopened.getinfo("one.txt").external_attr >> 16) & 0o7777 == 0o751


# -- the viewer's Save as, a write-protected .dbf, F7 and Alt+A in an archive ----


def test_the_viewers_save_as_writes_as_root(started, tmp_path, monkeypatch):
    from navigator.lib import viewer as viewer_model

    monkeypatch.setattr(SETTINGS.system, "root_timeout", 0)
    (tmp_path / "dos.txt").write_bytes(b"caf\x82\n")  # cp437's e-acute
    target = tmp_path / "out.txt"
    target.write_text("old")
    target.chmod(0o604)
    viewer_model.save_as(tmp_path / "dos.txt", target, "cp437", as_root=True)
    assert target.read_text() == "café\n" and target.stat().st_mode & 0o777 == 0o604
    assert not started.running  # let go after


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_a_write_protected_dbf_field_is_edited_as_root(helper, tmp_path, quiet_console, monkeypatch):
    from test_dbf import write_dbf

    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.lib.viewer import dbf
    from navigator.widgets.viewer.db_window import DBWindow

    monkeypatch.setattr(SETTINGS.system, "root_timeout", 0)
    people = write_dbf(tmp_path / "people.dbf")
    people.chmod(0o444)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))

    def window(a):
        found = a.shell.desktop.active_window
        return found if isinstance(found, DBWindow) else None

    def flip(a):
        w = window(a)
        w.viewer.go(record=0, field=3)  # OK, a logical: flipped without a box
        a.spawn(w.edit_field())

    seen: dict = {}
    run_app(app, [
        Until(lambda a: any(e.name == "people.dbf" for e in manager_of(a).active_panel.items)),
        put_cursor_on("people.dbf"), KeyEvent("f3"),
        Until(lambda a: window(a) is not None, timeout=5),
        flip,
        Until(lambda a: a.modal is not None, timeout=5),
        lambda a: seen.update(button=a.modal.ok.text),
        lambda a: a.spawn(a.modal.ok.press()),
        Until(lambda a: window(a).use_set is not None and a.modal is None, timeout=10),
        lambda a: seen.update(running=ELEVATION.running),  # held for the next field
        lambda a: window(a).close(),
        Until(lambda a: not ELEVATION.running, timeout=5),
    ])
    reread = dbf.DBFile(people)
    try:
        assert dbf.DBFile.raw(reread.record(0), reread.fields[3]) == "F"
    finally:
        reread.close()
    assert seen == {"button": "As ~r~oot", "running": True}
    assert people.stat().st_mode & 0o777 == 0o444


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_a_multi_rename_in_a_refused_archive_goes_on_as_root(helper, tmp_path, archives_closed):
    from navigator.lib.drives import archive, drive_of
    from navigator.lib.file_ops import multirename

    locked = tmp_path / "locked"
    locked.mkdir()
    zipped = make_zip(locked / "a.zip")
    locked.chmod(0o500)
    asked: list = []

    def asker(question):
        asked.append(question)
        assert isinstance(question, Failure) and question.elevate
        locked.chmod(0o700)
        assert ELEVATION.begin() == READY_STATE
        return AS_ROOT

    root = archive.open_archive(Location.of(zipped)).at("/")
    try:
        done = multirename.run([(root, "one.txt", "uno.txt")], multirename.RenameJob(asker=asker), drive_of)
    finally:
        locked.chmod(0o700)
    assert len(done) == 1 and len(asked) == 1
    assert zip_names(zipped) == ["uno.txt"]


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_a_multi_rename_in_an_archive_says_a_failure(tmp_path, archives_closed, monkeypatch):
    from navigator.lib.drives import archive, drive_of
    from navigator.lib.file_ops import multirename

    monkeypatch.setattr(SETTINGS.system, "elevate", "off")
    locked = tmp_path / "locked"
    locked.mkdir()
    zipped = make_zip(locked / "a.zip")
    locked.chmod(0o500)
    asked: list = []
    root = archive.open_archive(Location.of(zipped)).at("/")
    try:
        multirename.run([(root, "one.txt", "uno.txt")],
                        multirename.RenameJob(asker=lambda q: asked.append(q) or True), drive_of)
    finally:
        locked.chmod(0o700)
    assert len(asked) == 1 and isinstance(asked[0], Failure)  # no longer passed over in silence


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_mkdir_in_a_refused_archive_goes_on_as_root(helper, tmp_path, quiet_console, archives_closed):
    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.lib.drives import archive
    from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog

    locked = tmp_path / "locked"
    locked.mkdir()
    zipped = make_zip(locked / "a.zip")
    app = Navigator(locked, locked, terminal=FakeTerminal(80, 24))

    def into_archive(a):
        drive = archive.open_archive(Location.of(zipped))
        archive.hold(Location.of(zipped), manager_of(a).active_panel)
        manager_of(a).active_panel.location = drive.at("/")
        locked.chmod(0o500)

    try:
        run_app(app, [
            Until(lambda a: any(e.name == "a.zip" for e in manager_of(a).active_panel.items)),
            into_archive,
            Until(lambda a: any(e.name == "one.txt" for e in manager_of(a).active_panel.items), timeout=5),
            KeyEvent("f7"), Until(lambda a: isinstance(a.modal, MkdirDialog)),
            *[KeyEvent(c, c) for c in "sub"], KeyEvent("enter"),
            Until(lambda a: a.modal is not None and not isinstance(a.modal, MkdirDialog), timeout=5),
            press_ok_after(lambda: locked.chmod(0o700)),
            Until(lambda a: "sub/" in zip_names(zipped), timeout=10),
        ])
    finally:
        locked.chmod(0o700)


# -- browsing as root -------------------------------------------------------------


def test_the_root_site_lists_through_the_helper(started, tmp_path):
    from navigator.lib.drives import drive_of
    from navigator.lib.drives import root

    (tmp_path / "sub").mkdir()
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / ".hidden").write_text("h")
    holder = object()
    root.hold(holder)
    try:
        where = root.root_location(tmp_path)
        assert str(where) == f"root://{tmp_path}"
        entries, error, _ = drive_of(where).scan(where, False, "name", free=False)
        assert error is None
        assert [(e.name, e.is_dir) for e in entries] == [("..", True), ("sub", True), ("a.txt", False)]
        assert drive_of(where).stat(where / "a.txt").st_size == 1
    finally:
        assert root.leave(holder)
    from navigator.lib.drives import DriveGone

    with pytest.raises(DriveGone):
        drive_of(root.root_location(tmp_path))  # unmounted with its last holder


def test_copy_and_erase_between_the_root_site_and_the_disk(started, tmp_path):
    from navigator.lib.drives import root
    from navigator.lib.file_ops import fileerase

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.txt").write_text("alpha")
    (tmp_path / "dst").mkdir()
    holder = object()
    root.hold(holder)
    try:
        source = root.root_location(tmp_path / "src" / "a.txt")
        done = run(CopyRequest([source], str(tmp_path / "dst"), ASK, 0), CopyJob(asker=lambda q: None), tmp_path)
        assert done == [source] and (tmp_path / "dst" / "a.txt").read_text() == "alpha"
        gone = fileerase.run(fileerase.EraseRequest([source]), fileerase.EraseJob(asker=lambda q: fileerase.YES))
        assert gone == [source] and not (tmp_path / "src" / "a.txt").exists()
    finally:
        root.leave(holder)


@pytest.mark.skipif(IS_ROOT, reason="root is refused nothing")
def test_entering_an_unreadable_directory_offers_to_browse_as_root(helper, tmp_path, quiet_console, monkeypatch):
    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.lib.drives import root

    monkeypatch.setattr(SETTINGS.system, "root_timeout", 0)
    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "secret.txt").write_text("s")
    locked.chmod(0)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen: dict = {}

    def panel(a):
        return manager_of(a).active_panel

    def in_root(a):
        p = panel(a)
        return p.location.site == root.ROOT_SITE and any(e.name == "secret.txt" for e in p.items)

    def look(a):
        seen.update(where=str(panel(a).location), running=ELEVATION.running)

    try:
        run_app(app, [
            Until(lambda a: any(e.name == "locked" for e in panel(a).items)),
            put_cursor_on("locked"), KeyEvent("enter"),
            Until(lambda a: a.modal is not None, timeout=5),
            lambda a: seen.update(button=a.modal.ok.text),
            # The (unprivileged) helper must list it; the panel goes to root:
            # on the answer, whatever the mode is by then.
            press_ok_after(lambda: locked.chmod(0o755)),
            Until(in_root, timeout=10),
            look,
            lambda a: panel(a).go_up(),
            Until(lambda a: panel(a).location.is_local and any(e.name == "locked" for e in panel(a).items),
                  timeout=5),
            Until(lambda a: not ELEVATION.running, timeout=5),  # the last panel out let it go
        ])
    finally:
        locked.chmod(0o755)
    assert seen == {"button": "As ~r~oot", "where": f"root://{locked}", "running": True}


def test_a_file_fetched_from_the_root_site_goes_back_keeping_owner_and_mode(started, tmp_path):
    from navigator.lib.drives import root, usefile
    from navigator.lib.system.job import Job

    path = tmp_path / "conf"
    path.write_text("old\n")
    path.chmod(0o640)
    holder = object()
    root.hold(holder)
    try:
        origin = root.root_location(path)
        use = usefile.fetch([origin], Job())  # through the mounted root: drive, as F4 elsewhere does
        try:
            copy = use.copies[0]
            copy.local.write_text("new\n")
            usefile.upload([copy], Job())
        finally:
            usefile.discard(use)
    finally:
        root.leave(holder)
    assert path.read_text() == "new\n" and path.stat().st_mode & 0o777 == 0o640
    assert not any(p.name.startswith(".conf.nav-") for p in tmp_path.iterdir())  # no stray beside-file


def test_a_root_place_from_a_history_asks_to_open_root(helper, tmp_path, quiet_console):
    from conftest import FakeTerminal, Until, run_app
    from navigator.__main__ import Navigator
    from navigator.lib.drives import root

    place = tmp_path / "place"
    place.mkdir()
    (place / "inside.txt").write_text("x")
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen: dict = {}

    def panel(a):
        return manager_of(a).active_panel

    def go(a):
        assert not ELEVATION.running  # a new session's: nothing open yet
        a.spawn(manager_of(a)._go_to(panel(a), f"root://{place}"))

    run_app(app, [
        Until(lambda a: any(e.name == "place" for e in panel(a).items)),
        go,
        Until(lambda a: a.modal is not None, timeout=5),
        lambda a: seen.update(title=a.modal.title, prompt=a.modal.prompt, button=a.modal.ok.text),
        lambda a: a.spawn(a.modal.ok.press()),
        Until(lambda a: panel(a).location.site == root.ROOT_SITE
              and any(e.name == "inside.txt" for e in panel(a).items), timeout=10),
    ])
    assert seen == {"title": "Root access", "prompt": f"Open {place} as root?", "button": "As ~r~oot"}


def test_a_restored_root_panel_declined_shows_the_disk_instead(helper, tmp_path, quiet_console):
    from conftest import FakeTerminal, Until, run_app
    from navigator.__main__ import Navigator
    from navigator.lib.drives import root

    place = tmp_path / "place"
    place.mkdir()
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))

    def panel(a):
        return manager_of(a).active_panel

    seen: dict = {}
    run_app(app, [
        Until(lambda a: panel(a).items),
        lambda a: setattr(panel(a), "location", root.root_location(place)),  # as a saved desktop does
        Until(lambda a: a.modal is not None, timeout=5),
        lambda a: a.spawn(a.modal.cancel.press()),
        Until(lambda a: panel(a).location == Location.of(place), timeout=5),
        lambda a: None, lambda a: None,
        lambda a: seen.update(modal=a.modal, held=id(panel(a)) in root._HOLDERS),
    ])
    assert seen == {"modal": None, "held": False}  # not asked again, and nothing held


def test_a_restored_root_panel_reads_at_once_while_root_is_open(started, tmp_path, quiet_console):
    from conftest import FakeTerminal, Until, run_app
    from navigator.__main__ import Navigator
    from navigator.lib.drives import root

    place = tmp_path / "place"
    place.mkdir()
    (place / "inside.txt").write_text("x")
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))

    def panel(a):
        return manager_of(a).active_panel

    run_app(app, [
        Until(lambda a: panel(a).items),
        lambda a: setattr(panel(a), "location", root.root_location(place)),
        Until(lambda a: any(e.name == "inside.txt" for e in panel(a).items), timeout=10),
    ])
    assert app.modal is None


# -- find and the tree in a root panel --------------------------------------------


@pytest.fixture
def root_tree(tmp_path):
    (tmp_path / "sub" / "deep").mkdir(parents=True)
    (tmp_path / "sub" / "deep" / "x.conf").write_text("needle")
    (tmp_path / "sub" / "y.conf").write_text("hay")
    return tmp_path


def test_find_in_a_root_panel_searches_through_the_helper(started, root_tree, quiet_console):
    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.lib.drives import root
    from navigator.widgets.manager.find_file_dialog import FindFileDialog

    app = Navigator(root_tree, root_tree, terminal=FakeTerminal(100, 30))
    seen: dict = {}

    def panel(a):
        return manager_of(a).active_panel

    def ask(a):
        a.modal.mask.value = "*.conf"
        a.modal.text.value = "needle"

    run_app(app, [
        Until(lambda a: panel(a).items),
        lambda a: setattr(panel(a), "location", root.root_location(root_tree)),
        Until(lambda a: any(e.name == "sub" for e in panel(a).items), timeout=5),
        KeyEvent("f7", alt=True), Until(lambda a: isinstance(a.modal, FindFileDialog), timeout=5),
        ask, KeyEvent("enter"),
        Until(lambda a: panel(a).found is not None and not panel(a).found.live, timeout=10),
        lambda a: seen.update(found=[(str(e.directory), e.name) for e in panel(a).found.entries]),
    ])
    assert seen["found"] == [(f"root://{root_tree}/sub/deep", "x.conf")]


def test_the_tree_in_a_root_panel_lists_through_the_helper(started, root_tree, quiet_console):
    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.lib.drives import root

    app = Navigator(root_tree, root_tree, terminal=FakeTerminal(100, 30))
    seen: dict = {}

    def panel(a):
        return manager_of(a).active_panel

    def tree(a):
        return manager_of(a).tree

    run_app(app, [
        Until(lambda a: panel(a).items),
        lambda a: setattr(panel(a), "location", root.root_location(root_tree)),
        Until(lambda a: any(e.name == "sub" for e in panel(a).items), timeout=5),
        KeyEvent("t", ctrl=True),
        Until(lambda a: tree(a).visible and str(tree(a).selected_path) == f"root://{root_tree}", timeout=5),
        lambda a: seen.update(top=str(tree(a).root.data)),
    ])
    assert seen == {"top": "root:///"}


def test_a_readable_directory_chosen_in_the_tree_is_the_disks_own(started, root_tree, quiet_console):
    from conftest import FakeTerminal, Until, run_app
    from navigator.__main__ import Navigator
    from navigator.lib.drives import root
    from navml.widgets.dialog.tree_view import TreeNode

    app = Navigator(root_tree, root_tree, terminal=FakeTerminal(100, 30))

    def panel(a):
        return manager_of(a).active_panel

    class Chosen:
        node = TreeNode("sub", data=root.root_location(root_tree / "sub"))

    run_app(app, [
        Until(lambda a: panel(a).items),
        lambda a: setattr(panel(a), "location", root.root_location(root_tree)),
        Until(lambda a: any(e.name == "sub" for e in panel(a).items), timeout=5),
        lambda a: a.spawn(manager_of(a).on_tree_chosen(Chosen())),
        Until(lambda a: panel(a).location == Location.of(root_tree / "sub"), timeout=5),
    ])


def test_a_root_panel_refreshes_when_its_directory_changes(started, tmp_path, quiet_console, monkeypatch):
    from conftest import FakeTerminal, Until, run_app
    from navigator.__main__ import Navigator
    from navigator.lib.drives import root

    monkeypatch.setattr(root, "POLL_INTERVAL", 0.1)
    monkeypatch.setattr(SETTINGS.file_manager, "auto_refresh", True)
    (tmp_path / "old.txt").write_text("o")
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))

    def panel(a):
        return manager_of(a).active_panel

    run_app(app, [
        Until(lambda a: panel(a).items),
        lambda a: setattr(panel(a), "location", root.root_location(tmp_path)),
        Until(lambda a: any(e.name == "old.txt" for e in panel(a).items), timeout=5),
        lambda a: (tmp_path / "new.txt").write_text("n"),  # changed behind its back
        Until(lambda a: any(e.name == "new.txt" for e in panel(a).items), timeout=5),
    ])


def test_the_helper_writes_no_bytecode_as_root():
    for tool in ("sudo", "pkexec"):
        argv = ELEVATION.argv(tool)
        assert "-B" in argv and "-I" in argv, argv


def test_a_save_into_a_directory_the_user_cannot_enter(started, tmp_path, monkeypatch):
    """The real sudo check found it: the user's own lock check could not
    resolve a path inside a root-only directory and refused the save."""
    from navigator.lib.editor import save

    path = tmp_path / "conf.txt"
    path.write_text("old\n")

    def refused(target):
        raise PermissionError(errno.EACCES, "Permission denied", str(target))

    monkeypatch.setattr(save, "resolve", refused)  # the user cannot reach it
    calls: list = []
    real = ELEVATION.call_data

    def counted(op, *args, **kwargs):
        calls.append((op, kwargs.get("check_lock")))
        return real(op, *args, **kwargs)

    ELEVATION.call_data = counted  # type: ignore[method-assign]
    try:
        ROOT_DRIVE.write_file(path, [b"new\n"])
    finally:
        del ELEVATION.call_data
    assert path.read_text() == "new\n"
    assert ("write_text", True) in calls  # the helper looked for locks instead
