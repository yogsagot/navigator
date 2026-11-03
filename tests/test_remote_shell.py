"""Utilities > *Remote shell*: DN's ``cmTerminal`` as ``ssh -t`` to the server
the active panel is browsing over SFTP, in a command window.

The end-to-end tests put a fake ``ssh`` first on ``PATH`` -- a script that
prints its arguments and waits -- and run it on a real pty, as
``test_terminal_window.py`` does.
"""

from __future__ import annotations

import shlex
from pathlib import PurePosixPath

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.drives import remote_shell
from navigator.lib.drives.location import Location, Site
from navigator.widgets.shell.commands import Terminal

SITE = Site("sftp", "bob", "example.org", 2222)


def words(command: str) -> list[str]:
    return shlex.split(command)


def test_the_command_names_user_port_and_host_and_starts_in_the_directory():
    command = remote_shell.command(Location(SITE, PurePosixPath("/srv/it's a dir")))
    argv = words(command)
    assert argv[:7] == ["ssh", "-t", "-p", "2222", "-l", "bob", "--"]
    assert argv[7] == "example.org"
    # What the remote shell is given parses back to cd into the directory.
    remote = shlex.split(argv[8])
    assert remote[:2] == ["cd", "/srv/it's a dir"]
    assert argv[8].endswith('exec "${SHELL:-/bin/sh}" -l')


def test_no_user_or_port_leaves_ssh_config_to_say():
    argv = words(remote_shell.command(Location(Site("sftp", "", "box"), PurePosixPath("/"))))
    assert argv[:4] == ["ssh", "-t", "--", "box"]


def test_login_for_the_title():
    assert remote_shell.login(SITE) == "bob@example.org:2222"
    assert remote_shell.login(Site("sftp", "", "::1", 22)) == "[::1]:22"
    assert remote_shell.login(Site("sftp", "", "::1")) == "::1"


def test_target_takes_only_ssh_servers_and_an_archive_s_directory():
    there = Location(SITE, PurePosixPath("/srv"))
    assert remote_shell.target(there) is there
    assert remote_shell.target(Location.of("/tmp")) is None
    assert remote_shell.target(Location(Site("ftp", "", "h"), PurePosixPath("/"))) is None
    inside = Location(Site("arc"), PurePosixPath("/docs"), Location(SITE, PurePosixPath("/srv/x.zip")))
    assert remote_shell.target(inside) == Location(SITE, PurePosixPath("/srv"))
    local_archive = Location(Site("arc"), PurePosixPath("/"), Location.of("/tmp/x.zip"))
    assert remote_shell.target(local_archive) is None


def make(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr("navigator.lib.system.tempdir.private_dir", lambda: tmp_path / "private")
    (tmp_path / "private").mkdir(exist_ok=True)
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))


def test_not_refused_on_a_local_panel_or_with_no_manager(tmp_path, monkeypatch):
    monkeypatch.setattr(remote_shell, "program", lambda: "/usr/bin/ssh")
    app = make(tmp_path, monkeypatch)
    seen = {}
    run_app(app, [lambda a: seen.update(why=a.shell.refusal(Terminal()))])
    assert seen["why"] == ""


def test_refused_without_ssh(tmp_path, monkeypatch):
    app = make(tmp_path, monkeypatch)
    monkeypatch.setattr(remote_shell, "program", lambda: None)
    seen = {}
    run_app(app, [lambda a: seen.update(why=a.shell.refusal(Terminal()))])
    assert seen["why"] == "The ssh command is not installed"


def windows(app):
    from navigator.widgets.shell.terminal_window import TerminalWindow

    return [w for w in app.shell.desktop.windows() if isinstance(w, TerminalWindow)]


def text(window) -> str:
    screen = window.view.screen
    surface = screen.surface
    return "\n".join("".join(surface.get(x, y)[0] or " " for x in range(screen.columns)).rstrip()
                     for y in range(screen.lines))


@pytest.fixture
def fake_ssh(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "ssh"
    script.write_text('#!/bin/sh\nfor a in "$@"; do printf "<%s>\\n" "$a"; done\nexec sleep 30\n')
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{__import__('os').environ['PATH']}")
    return script


def test_opens_ssh_in_a_window_and_brings_it_back_while_it_runs(tmp_path, monkeypatch, fake_ssh):
    app = make(tmp_path, monkeypatch)
    monkeypatch.setattr("navigator.widgets.shell.shell.Shell.remote_shell_location",
                        lambda self: Location(SITE, PurePosixPath("/srv/a b")))
    seen = {}

    def command(a):
        a.spawn(a.run_command(Terminal))

    def showing(a):
        found = windows(a)
        return bool(found) and "<example.org>" in text(found[0])

    def look(a):
        window = windows(a)[0]
        seen.update(text=text(window), title=window.title, site=window.remote_site, busy=window.view.busy)

    def manager(a):
        from navigator.widgets.drives.ssh_link_dialog import SshLinkDialog

        return isinstance(a.modal, SshLinkDialog)

    def lines(a):
        seen.update(title_box=a.modal.title, host=a.modal.host.value, directory=a.modal.directory.value)

    def again(a):
        seen["window"] = windows(a)[0]
        command(a)

    run_app(app, [command, Until(manager), lines, KeyEvent("enter"), Until(showing), look, again,
                  lambda a: seen.update(count=len(windows(a)), top=a.shell.desktop.active_window is seen["window"],
                                        box=a.modal is not None)])
    # The box opens on the panel's server, and its Connect is Enter.
    assert seen["title_box"] == "Remote shell" and seen["host"] == "example.org"
    assert seen["directory"] == "/srv/a b"
    # Asked again while it runs: the window comes forward, no box.
    assert not seen["box"]
    assert "<-t>" in seen["text"] and "<-p>" in seen["text"] and "<bob>" in seen["text"]
    assert "<cd '/srv/a b' 2>/dev/null; exec \"${SHELL:-/bin/sh}\" -l>" in seen["text"].replace("\n", "")
    assert seen["title"] == "ssh bob@example.org:2222"
    assert seen["site"] == SITE and seen["busy"]
    assert seen["count"] == 1 and seen["top"]


def test_with_no_ssh_panel_the_box_s_lines_say_where(tmp_path, monkeypatch, fake_ssh):
    from navigator.lib.drives import profiles
    from navigator.widgets.drives.ssh_link_dialog import SshLinkDialog

    profiles.save("box", "sftp", "box.lan", "root", 0, "")
    app = make(tmp_path, monkeypatch)
    seen = {}

    def showing(a):
        found = windows(a)
        return bool(found) and "<box.lan>" in text(found[0])

    run_app(app, [lambda a: a.spawn(a.run_command(Terminal)), Until(lambda a: isinstance(a.modal, SshLinkDialog)),
                  lambda a: seen.update(items=list(a.modal.links.items), empty=a.modal.host.value == ""),
                  lambda a: a.modal.links.focus(), KeyEvent(" "), KeyEvent("enter"), Until(showing),
                  lambda a: seen.update(text=text(windows(a)[0]).replace("\n", ""), title=windows(a)[0].title)])
    # Opened empty; Space on the saved connection chose it, Enter connected.
    assert seen["items"] == ["box"] and seen["empty"]
    assert "<-l><root><--><box.lan><exec \"${SHELL:-/bin/sh}\" -l>" in seen["text"]
    assert seen["title"] == "ssh root@box.lan"


def test_home_leaves_out_the_cd():
    argv = words(remote_shell.command(Location(SITE, PurePosixPath("."))))
    assert argv[-1] == 'exec "${SHELL:-/bin/sh}" -l'


def test_ended_well_is_every_ssh_exit_but_its_own_failure():
    assert remote_shell.ended_well(0)
    assert remote_shell.ended_well(1 << 8)  # the remote shell's last command failed
    assert not remote_shell.ended_well(255 << 8)  # ssh itself: refused, unreachable, not let in
    assert not remote_shell.ended_well(9)  # killed by a signal


@pytest.mark.parametrize("code, closed", [(0, True), (1, True), (255, False)])
def test_the_window_goes_when_the_connection_ends_but_stays_for_ssh_s_failure(tmp_path, monkeypatch, code, closed):
    from navigator.widgets.drives.ssh_link_dialog import SshLinkDialog

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "ssh"
    # Waits for a line, as a shell waits for Ctrl+D, then ends with *code*.
    script.write_text(f'#!/bin/sh\necho ready\nread line\nexit {code}\n')
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{__import__('os').environ['PATH']}")
    app = make(tmp_path, monkeypatch)
    seen = {}

    def connect(a):
        a.modal.host.value = "box.lan"

    run_app(app, [lambda a: a.spawn(a.run_command(Terminal)), Until(lambda a: isinstance(a.modal, SshLinkDialog)),
                  connect, KeyEvent("enter"), Until(lambda a: windows(a) and "ready" in text(windows(a)[0])),
                  lambda a: seen.update(window=windows(a)[0]), KeyEvent("enter"),
                  Until(lambda a: seen["window"].view.status is not None),
                  lambda a: seen.update(open=bool(windows(a)), title=seen["window"].title)])
    assert seen["open"] is not closed
    if not closed:
        assert seen["title"] == "ssh box.lan - exit status 255"
