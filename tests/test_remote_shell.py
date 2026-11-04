"""Utilities > *Remote shell*: DN's ``cmTerminal`` as ``ssh -t`` to a server --
or ``docker exec -it`` / ``adb shell`` -- chosen in that protocol's link
manager, in a command window.  Nothing is taken from the panel.

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
from navigator.widgets.shell.commands import AdbShell, DockerShell, Terminal

SITE = Site("sftp", "bob", "example.org", 2222)


def words(command: str) -> list[str]:
    return shlex.split(command)


def test_the_command_names_user_port_and_host_and_starts_in_the_directory():
    command = remote_shell.command(Location(SITE, PurePosixPath("/srv/it's a dir")))
    argv = words(command)
    # ``-Y`` is ``[remote] ssh_options``' default: X11 forwarding, for the clipboard there.
    assert argv[:8] == ["ssh", "-t", "-Y", "-p", "2222", "-l", "bob", "--"]
    assert argv[8] == "example.org"
    # What the remote shell is given parses back to cd into the directory.
    remote = shlex.split(argv[9])
    assert remote[:2] == ["cd", "/srv/it's a dir"]
    assert argv[9].endswith('exec "${SHELL:-/bin/sh}" -l')


def test_no_user_or_port_leaves_ssh_config_to_say():
    argv = words(remote_shell.command(Location(Site("sftp", "", "box"), PurePosixPath("/"))))
    assert argv[:5] == ["ssh", "-t", "-Y", "--", "box"]


def test_login_for_the_title():
    assert remote_shell.login(SITE) == "bob@example.org:2222"
    assert remote_shell.login(Site("sftp", "", "::1", 22)) == "[::1]:22"
    assert remote_shell.login(Site("sftp", "", "::1")) == "::1"


def make(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr("navigator.lib.system.tempdir.private_dir", lambda: tmp_path / "private")
    (tmp_path / "private").mkdir(exist_ok=True)
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))


def test_not_refused_on_a_local_panel_or_with_no_manager(tmp_path, monkeypatch):
    monkeypatch.setattr(remote_shell, "program", lambda scheme="sftp": "/usr/bin/ssh")
    app = make(tmp_path, monkeypatch)
    seen = {}
    run_app(app, [lambda a: seen.update(why=a.shell.refusal(Terminal()))])
    assert seen["why"] == ""


def test_refused_without_ssh(tmp_path, monkeypatch):
    app = make(tmp_path, monkeypatch)
    monkeypatch.setattr(remote_shell, "program", lambda scheme="sftp": None)
    seen = {}
    run_app(app, [lambda a: seen.update(why=a.shell.refusal(Terminal()), docker=a.shell.refusal(DockerShell()),
                                        adb=a.shell.refusal(AdbShell()))])
    assert seen["why"] == "The ssh command is not installed"
    assert seen["docker"] == "The docker command is not installed"
    assert seen["adb"] == "The adb command is not installed"


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


def test_opens_ssh_in_a_window_and_finds_it_while_it_runs(tmp_path, monkeypatch, fake_ssh):
    from navigator.widgets.drives.link_manager import LinkManagerDialog

    app = make(tmp_path, monkeypatch)
    seen = {}

    def command(a):
        a.spawn(a.run_command(Terminal))

    def manager(a):
        return isinstance(a.modal, LinkManagerDialog)

    def fill(a):
        seen.setdefault("title_box", a.modal.title)
        seen.setdefault("empty", a.modal.host.value == "")
        a.modal.host.value = "example.org"
        a.modal.user.value = "bob"
        a.modal.port.value = "2222"
        a.modal.directory.value = "/srv/a b"

    def showing(a):
        found = windows(a)
        return bool(found) and "<example.org>" in text(found[0])

    def look(a):
        window = windows(a)[0]
        seen.update(text=text(window), title=window.title, site=window.remote_site, busy=window.view.busy,
                    window=window)

    def again(a):
        # Chosen again while it runs (``open_remote_shell`` past its box): no second window.
        seen["again"] = a.shell._running_remote_shell(SITE)

    run_app(app, [command, Until(manager), fill, KeyEvent("enter"), Until(showing), look, again,
                  lambda a: seen.update(count=len(windows(a)), top=a.shell.desktop.active_window is seen["window"])])
    # The box opens empty, whatever the panel shows; its Connect is Enter.
    assert seen["title_box"] == "Remote shell" and seen["empty"]
    assert "<-t>" in seen["text"] and "<-p>" in seen["text"] and "<bob>" in seen["text"]
    assert "<cd '/srv/a b' 2>/dev/null; exec \"${SHELL:-/bin/sh}\" -l>" in seen["text"].replace("\n", "")
    assert seen["title"] == "ssh bob@example.org:2222"
    assert seen["site"] == SITE and seen["busy"]
    # The same server chosen again while it runs: that window comes forward.
    assert seen["again"] is seen["window"] and seen["count"] == 1 and seen["top"]


def test_with_no_ssh_panel_the_box_s_lines_say_where(tmp_path, monkeypatch, fake_ssh):
    from navigator.lib.drives import profiles
    from navigator.widgets.drives.link_manager import LinkManagerDialog

    profiles.save("box", "sftp", "box.lan", "root", 0, "")
    app = make(tmp_path, monkeypatch)
    seen = {}

    def showing(a):
        found = windows(a)
        return bool(found) and "<box.lan>" in text(found[0])

    run_app(app, [lambda a: a.spawn(a.run_command(Terminal)), Until(lambda a: isinstance(a.modal, LinkManagerDialog)),
                  lambda a: seen.update(items=list(a.modal.links.items), empty=a.modal.host.value == ""),
                  lambda a: a.modal.links.focus(), KeyEvent(" "), KeyEvent("enter"), Until(showing),
                  lambda a: seen.update(text=text(windows(a)[0]).replace("\n", ""), title=windows(a)[0].title)])
    # Opened empty; Space on the saved connection chose it, Enter connected.
    assert seen["items"] == ["box"] and seen["empty"]
    assert "<-Y><-l><root><--><box.lan><exec \"${SHELL:-/bin/sh}\" -l>" in seen["text"]
    assert seen["title"] == "ssh root@box.lan"


def test_home_leaves_out_the_cd():
    argv = words(remote_shell.command(Location(SITE, PurePosixPath("."))))
    assert argv[-1] == 'exec "${SHELL:-/bin/sh}" -l'


def test_ended_well_is_every_ssh_exit_but_its_own_failure():
    assert remote_shell.ended_well(0)
    assert remote_shell.ended_well(1 << 8)  # the remote shell's last command failed
    assert not remote_shell.ended_well(255 << 8)  # ssh itself: refused, unreachable, not let in
    assert not remote_shell.ended_well(9)  # killed by a signal
    # docker exec's own failures: the daemon's (125), nothing to run (126, 127).
    assert remote_shell.ended_well(255 << 8, "docker") and not remote_shell.ended_well(125 << 8, "docker")
    assert not remote_shell.ended_well(255 << 8, "adb")


def test_a_container_s_shell_is_docker_exec_in_its_directory():
    argv = words(remote_shell.command(Location(Site("docker", "www", "Web"), PurePosixPath("/srv/a b"))))
    assert argv == ["docker", "exec", "-it", "-u", "www", "-w", "/srv/a b", "Web", "sh", "-c",
                    'exec "${SHELL:-/bin/sh}" -l']
    argv = words(remote_shell.command(Location(Site("podman", "", "box"), PurePosixPath("."))))
    assert argv[:4] == ["podman", "exec", "-it", "box"]
    assert remote_shell.title(Site("docker", "www", "Web")) == "docker exec -u www Web"


def test_a_device_s_shell_is_adb_shell():
    argv = words(remote_shell.command(Location(Site("adb", "", "192.168.1.5", 5555), PurePosixPath("/sdcard/a b"))))
    assert argv[:5] == ["adb", "-s", "192.168.1.5:5555", "shell", "-t"]
    assert shlex.split(argv[5]) == ["cd", "/sdcard/a b", "2>/dev/null;", "exec", "sh"]
    assert words(remote_shell.command(Location(Site("adb", "", "R5"), PurePosixPath(".")))) == [
        "adb", "-s", "R5", "shell", "-t"]
    assert remote_shell.title(Site("adb", "", "R5")) == "adb shell R5"


def test_docker_s_shell_opens_from_its_own_manager(tmp_path, monkeypatch):
    """Utilities > Remote shell > Docker container: Docker's manager in its
    shell mode, and Connect runs ``docker exec -it`` in a window."""
    from navigator.widgets.drives.link_manager import LinkManagerDialog

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "docker"
    script.write_text('#!/bin/sh\nif [ "$1" = ps ]; then echo \'{"Names":"web","Image":"nginx"}\'; exit 0; fi\n'
                      'for a in "$@"; do printf "<%s>\\n" "$a"; done\nexec sleep 30\n')
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{__import__('os').environ['PATH']}")
    app = make(tmp_path, monkeypatch)
    seen = {}

    def manager(a):
        return isinstance(a.modal, LinkManagerDialog) and bool(a.modal.live)

    def choose(a):
        seen.update(title=a.modal.title, rows=list(a.modal.links.items))
        a.modal.links.focus()
        a.modal.links.cursor = 1

    def showing(a):
        found = windows(a)
        return bool(found) and "<web>" in text(found[0])

    run_app(app, [lambda a: a.spawn(a.run_command(DockerShell)), Until(manager), choose, KeyEvent("enter"),
                  Until(showing), lambda a: seen.update(text=text(windows(a)[0]).replace("\n", ""),
                                                        window=windows(a)[0].title)])
    assert seen["title"] == "Remote shell: Docker container"
    assert seen["rows"] == ["── Running ──", "web  nginx"]
    assert "<exec><-it><web><sh><-c>" in seen["text"]
    assert seen["window"] == "docker exec web"


@pytest.mark.parametrize("code, closed", [(0, True), (1, True), (255, False)])
def test_the_window_goes_when_the_connection_ends_but_stays_for_ssh_s_failure(tmp_path, monkeypatch, code, closed):
    from navigator.widgets.drives.link_manager import LinkManagerDialog

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

    run_app(app, [lambda a: a.spawn(a.run_command(Terminal)), Until(lambda a: isinstance(a.modal, LinkManagerDialog)),
                  connect, KeyEvent("enter"), Until(lambda a: windows(a) and "ready" in text(windows(a)[0])),
                  lambda a: seen.update(window=windows(a)[0]), KeyEvent("enter"),
                  Until(lambda a: seen["window"].view.status is not None),
                  lambda a: seen.update(open=bool(windows(a)), title=seen["window"].title)])
    assert seen["open"] is not closed
    if not closed:
        assert seen["title"] == "ssh box.lan - exit status 255"


def test_the_setting_then_the_connection_s_own_options_come_before_the_host(monkeypatch):
    from navigator.settings import SETTINGS

    monkeypatch.setattr(SETTINGS.remote, "ssh_options", "-Y -o 'ServerAliveInterval 30'")
    argv = words(remote_shell.command(Location(Site("sftp", "", "box"), PurePosixPath(".")), "-A -J jump"))
    assert argv[:9] == ["ssh", "-t", "-Y", "-o", "ServerAliveInterval 30", "-A", "-J", "jump", "--"]
    assert argv[9] == "box"


def test_no_setting_and_unclosed_quotes_still_make_a_command(monkeypatch):
    from navigator.settings import SETTINGS

    monkeypatch.setattr(SETTINGS.remote, "ssh_options", "")
    argv = words(remote_shell.command(Location(Site("sftp", "", "box"), PurePosixPath(".")), "-o 'broken"))
    assert argv[:5] == ["ssh", "-t", "-o", "'broken", "--"]


def test_a_connection_s_options_reach_its_remote_shell(tmp_path, monkeypatch, fake_ssh):
    from navigator.lib.drives import profiles
    from navigator.widgets.drives.link_manager import LinkManagerDialog

    profiles.save("box", "sftp", "box.lan", "root", 0, "", "-A")
    app = make(tmp_path, monkeypatch)
    seen = {}

    def showing(a):
        found = windows(a)
        return bool(found) and "<box.lan>" in text(found[0])

    run_app(app, [lambda a: a.spawn(a.run_command(Terminal)), Until(lambda a: isinstance(a.modal, LinkManagerDialog)),
                  lambda a: seen.update(field=a.modal.options.visible), lambda a: a.modal.links.focus(), KeyEvent(" "),
                  lambda a: seen.update(options=a.modal.options.value), KeyEvent("enter"), Until(showing),
                  lambda a: seen.update(text=text(windows(a)[0]).replace("\n", ""))])
    assert seen["field"] and seen["options"] == "-A"
    assert "<-t><-Y><-A><-l><root><--><box.lan>" in seen["text"]
