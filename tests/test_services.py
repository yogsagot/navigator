"""Utilities > Services with systemd: reading ``systemctl``, the root helper's ops, the window, F3 and F4."""

from __future__ import annotations

import errno
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from navkit.events import KeyEvent

from conftest import Until, run_app

from navigator.lib.system import services
from navigator.lib.system.services import Unit, common, systemd


def completed(stdout: str = "", returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


UNITS_JSON = json.dumps([
    {"unit": "cron.service", "load": "loaded", "active": "active", "sub": "running", "description": "Regular jobs"},
    {"unit": "getty@tty1.service", "load": "loaded", "active": "active", "sub": "running",
     "description": "Getty on tty1"},
    {"unit": "broken.service", "load": "loaded", "active": "failed", "sub": "failed", "description": "Broken"},
])
FILES_JSON = json.dumps([
    {"unit_file": "cron.service", "state": "enabled", "preset": "enabled"},
    {"unit_file": "getty@.service", "state": "enabled", "preset": "enabled"},
    {"unit_file": "idle.service", "state": "disabled", "preset": None},
    {"unit_file": "broken.service", "state": "static", "preset": None},
])


def fake_systemctl(calls: list[list[str]], json_works: bool = True):
    def run(argv):
        calls.append(argv)
        if "--output=json" in argv:
            if not json_works:
                return completed(returncode=1, stderr="Unknown output 'json'")
            return completed(UNITS_JSON if "list-units" in argv else FILES_JSON)
        if "list-units" in argv:
            return completed("● cron.service loaded active running Regular jobs\n"
                             "idle.service loaded inactive dead\n")
        return completed("cron.service enabled enabled\nidle.service disabled -\n")
    return run


def test_the_loaded_units_and_the_installed_ones_are_merged_and_templates_left_out(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", fake_systemctl(calls))
    found = {unit.name: unit for unit in services.gather()}
    assert set(found) == {"cron.service", "getty@tty1.service", "broken.service", "idle.service"}
    assert found["cron.service"].startup == "enabled" and found["cron.service"].running
    # An instance takes its template's state; one installed but not loaded is inactive.
    assert found["getty@tty1.service"].startup == "enabled"
    assert (found["idle.service"].active, found["idle.service"].sub) == ("inactive", "dead")
    assert found["broken.service"].failed
    assert all("--type=service" in argv for argv in calls) and all("--user" not in argv for argv in calls)


def test_user_units_and_every_type_are_asked_for_and_plain_columns_read_without_json(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", fake_systemctl(calls, json_works=False))
    found = {unit.name: unit for unit in services.gather(user=True, all_types=True)}
    assert found["cron.service"].description == "Regular jobs" and found["cron.service"].user
    assert found["idle.service"].startup == "disabled" and found["idle.service"].description == ""
    assert all(argv[:2] == ["systemctl", "--user"] and "--type=service" not in argv for argv in calls)


def test_ordered_matches_and_valid_names():
    a = Unit("b.service", active="active", sub="running", startup="enabled", description="Zeta")
    b = Unit("A.service", active="inactive", startup="disabled", description="alpha")
    c = Unit("c.timer", active="active", sub="waiting", startup="enabled", description="Gamma")
    assert [u.name for u in services.ordered([a, b, c], "name", False)] == ["A.service", "b.service", "c.timer"]
    assert [u.name for u in services.ordered([a, b, c], "active", False)] == ["b.service", "c.timer", "A.service"]
    assert [u.name for u in services.ordered([a, b, c], "description", True)] == ["b.service", "c.timer",
                                                                                   "A.service"]
    assert services.matches(b, "ALPH") and services.matches(c, "timer") and not services.matches(a, "gamma")
    assert systemd.valid_unit("getty@tty1.service") and systemd.valid_unit("sys-kernel-debug.mount")
    for bad in ("-H.service", "a b.service", "x;rm.service", "noext", ""):
        assert not systemd.valid_unit(bad), bad


def test_act_asks_no_password_and_a_polkit_refusal_is_eperm(monkeypatch):
    from navigator.lib.system.elevate import refused

    calls: list[list[str]] = []

    def run(argv):
        calls.append(argv)
        if argv[-1] == "denied.service":
            return completed(returncode=1, stderr="Failed to start denied.service: Access denied\n")
        return completed(returncode=5, stderr="Unit nope.service not found.")

    monkeypatch.setattr(common, "run", run)
    with pytest.raises(OSError) as denied:
        services.act(Unit("denied.service"), "start")
    assert denied.value.errno == errno.EPERM and refused(denied.value)
    assert calls[0] == ["systemctl", "--no-ask-password", "start", "--", "denied.service"]
    with pytest.raises(OSError) as missing:
        services.act(Unit("nope.service", user=True), "stop")
    assert missing.value.errno == errno.EIO and "not found" in missing.value.strerror
    assert calls[1][:2] == ["systemctl", "--user"]
    with pytest.raises(OSError) as invalid:
        services.act(Unit("x.service"), "kill")
    assert invalid.value.errno == errno.EINVAL and len(calls) == 2


# -- the root helper ---------------------------------------------------------


def test_the_helpers_service_op_runs_only_a_listed_verb_of_a_known_manager_on_a_valid_name(monkeypatch):
    from navigator.lib.system import roothelper

    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", lambda argv: calls.append(argv) or completed())
    helper = roothelper._Helper()
    assert {"service", "after_edit", "journal_follow", "journal_stop"} <= roothelper.OPS
    assert not {"systemctl", "daemon_reload"} & roothelper.OPS
    for manager, verb, unit in (("systemd", "poweroff", "cron.service"), ("systemd", "start", "--root=/x"),
                                ("systemd", "start", "a b.service"), ("upstart", "start", "cron.service"),
                                ("openrc", "mask", "sshd")):
        with pytest.raises(OSError) as refused:
            helper.service(manager, verb, unit)
        assert refused.value.errno == errno.EINVAL
    assert calls == []
    helper.service("systemd", "restart", "cron.service")
    assert calls == [["systemctl", "--no-ask-password", "restart", "--", "cron.service"]]


LINES = "import sys, time\nfor n in range(10000):\n    print('line', n, flush=True)\n    time.sleep(0.05)\n"


def test_the_helper_follows_a_journal_into_the_users_file_and_stops_it(tmp_path, monkeypatch):
    from navigator.lib.system import roothelper

    monkeypatch.setattr(systemd, "journal_argv", lambda name, user, lines: [sys.executable, "-c", LINES])
    helper = roothelper._Helper(trusted=frozenset({os.getuid()}))
    out = tmp_path / "journal.log"
    with pytest.raises(OSError):
        helper.journal_follow("cron.service", str(out), 10)  # never created by the helper
    out.write_bytes(b"")
    with pytest.raises(OSError):
        helper.journal_follow("-x.service", str(out), 10)
    pid = helper.journal_follow("cron.service", str(out), 10)
    process = helper.journals[pid]
    deadline = time.monotonic() + 5
    while not out.stat().st_size and time.monotonic() < deadline:
        time.sleep(0.05)
    assert out.read_text().startswith("line 0")
    helper.journal_stop(12345678)  # not one of its own: nothing
    helper.journal_stop(pid)
    assert process.poll() is not None and not helper.journals


# -- the window --------------------------------------------------------------


def fake_units() -> list[Unit]:
    return [
        Unit("cron.service", "loaded", "active", "running", "enabled", "Regular background program processing"),
        Unit("idle.service", "", "inactive", "dead", "disabled", ""),
        Unit("broken.service", "loaded", "failed", "failed", "static", "Broken thing"),
    ]


def service_run(where, monkeypatch, *actions, reads=None, units=None, manager="systemd"):
    from test_nav import navigator

    from navigator.settings import SETTINGS

    def gather(user=False, all_types=False):
        if reads is not None:
            reads.append((user, all_types))
        return (units or fake_units)()

    monkeypatch.setattr(services, "gather", gather)
    monkeypatch.setattr(SETTINGS.services, "refresh", 0)
    monkeypatch.setattr(SETTINGS.services, "manager", manager)
    app = navigator(where)

    def open_it(a):
        from navigator.widgets.shell.commands import OpenServiceWindow

        a.spawn(a.run_command(OpenServiceWindow))

    def listed(a):
        window = a.shell.desktop.active_window
        return getattr(window, "units", None) is not None and bool(window.units.items)

    run_app(app, [open_it, Until(listed), *actions, lambda a: None])
    return app


def names(a) -> list[str]:
    return [unit.name for unit in a.shell.desktop.active_window.units.items]


def test_the_window_lists_by_name_filters_and_keeps_the_cursor_by_name(tmp_path, monkeypatch):
    seen = []

    def look(a):
        window = a.shell.desktop.active_window
        seen.append((names(a), window.units.selected.name, window.status.text))

    def to_idle(a):
        a.shell.desktop.active_window.units.cursor = names(a).index("idle.service")

    service_run(tmp_path, monkeypatch, look, to_idle, KeyEvent("l", ctrl=True), look,
                *[KeyEvent(c, char=c) for c in "brok"], look)
    assert seen[0][0] == ["broken.service", "cron.service", "idle.service"]
    assert seen[0][2] == "3 units, 1 running, 1 failed"
    # By state, the cursor still on the unit it was on.
    assert seen[1][:2] == (["cron.service", "broken.service", "idle.service"], "idle.service")
    assert seen[2][:2] == (["broken.service"], "broken.service")
    assert seen[2][2] == "1 of 3 units match the filter"


def test_user_units_and_all_types_read_again(tmp_path, monkeypatch):
    reads: list[tuple[bool, bool]] = []
    service_run(tmp_path, monkeypatch, KeyEvent("u", ctrl=True), Until(lambda a: len(reads) >= 2),
                KeyEvent("a", ctrl=True), Until(lambda a: len(reads) >= 3), reads=reads)
    assert reads[:3] == [(False, False), (True, False), (True, True)]


def test_f5_starts_and_f8_asks_before_stopping(tmp_path, monkeypatch):
    done: list[tuple[str, str]] = []
    monkeypatch.setattr(services, "act", lambda unit, verb: done.append((unit.name, verb)))
    service_run(tmp_path, monkeypatch, KeyEvent("f5"), Until(lambda a: bool(done)),
                KeyEvent("f8"), Until(lambda a: a.modal is not None), KeyEvent("enter"),
                Until(lambda a: len(done) >= 2), KeyEvent("e", ctrl=True), Until(lambda a: len(done) >= 3))
    assert done == [("broken.service", "start"), ("broken.service", "stop"), ("broken.service", "enable")]


def test_a_refused_start_is_offered_as_root_and_done_by_the_helper(tmp_path, monkeypatch):
    from navigator.lib.system import elevate
    from navigator.widgets.file_ops import as_root

    asked = []
    root_calls = []

    def refuse(unit, verb):
        raise PermissionError(errno.EPERM, "Interactive authentication required.")

    async def yes(app, message, **kwargs):
        asked.append(message)
        return True

    monkeypatch.setattr(services, "act", refuse)
    monkeypatch.setattr(elevate.ELEVATION, "available", lambda: True)
    original = elevate.ELEVATION.call

    def call(op, payload=b"", **args):
        if op != "service":
            return original(op, payload, **args)
        root_calls.append((op, args))
        return None

    monkeypatch.setattr(elevate.ELEVATION, "call", call)
    monkeypatch.setattr(elevate.ELEVATION, "release", lambda: None)
    monkeypatch.setattr(as_root, "ask_as_root", yes)
    service_run(tmp_path, monkeypatch, KeyEvent("f6"), Until(lambda a: bool(root_calls)))
    assert "broken.service" in asked[0]
    assert root_calls == [("service", {"manager": "systemd", "verb": "restart", "unit": "broken.service"})]


def test_f3_follows_the_journal_in_the_viewer_and_closing_it_stops_journalctl(tmp_path, monkeypatch):
    from navigator.lib.system import tempdir
    from navigator.settings import SETTINGS
    from navigator.widgets.shell.service_window.journal_window import JournalWindow

    started = []

    def argv(name, user, lines):
        started.append((name, user, lines))
        return [sys.executable, "-c", LINES]

    monkeypatch.setattr(systemd, "journal_argv", argv)
    monkeypatch.setattr(systemd, "can_read_journal", lambda unit: True)
    (tmp_path / "tmp").mkdir()
    monkeypatch.setattr(tempdir, "private_dir", lambda: tmp_path / "tmp")
    monkeypatch.setattr(SETTINGS.services, "journal_lines", 50)
    seen = {}

    def journal(a):
        window = a.shell.desktop.active_window
        return isinstance(window, JournalWindow) and window.viewer.follow and window.viewer.size > 0

    def look(a):
        window = a.shell.desktop.active_window
        seen["title"] = window.title
        seen["path"] = window.viewer.path
        seen["window"] = window
        window.close()

    service_run(tmp_path, monkeypatch, KeyEvent("f3"), Until(journal, timeout=10), look)
    window = seen["window"]
    assert started == [("broken.service", False, 50)]
    assert seen["title"] == "Journal: broken.service"
    window.stopping.join(timeout=10)
    assert not os.path.exists(str(seen["path"]))


# -- F4: the unit's file -----------------------------------------------------


def test_unit_file_is_the_fragment_and_a_masked_unit_has_none(monkeypatch):
    calls: list[list[str]] = []
    answers = {"cron.service": "/usr/lib/systemd/system/cron.service\n", "masked.service": "/dev/null\n"}
    monkeypatch.setattr(common, "run", lambda argv: calls.append(argv) or completed(answers[argv[-1]]))
    assert str(systemd.unit_file(Unit("cron.service"))) == "/usr/lib/systemd/system/cron.service"
    assert calls[0] == ["systemctl", "show", "--property=FragmentPath", "--value", "--", "cron.service"]
    with pytest.raises(OSError) as none:
        systemd.unit_file(Unit("masked.service", user=True))
    assert none.value.errno == errno.ENOENT and calls[1][:2] == ["systemctl", "--user"]


def test_the_helpers_after_edit_reloads_systemd_and_does_nothing_for_openrc(monkeypatch):
    from navigator.lib.system import roothelper

    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", lambda argv: calls.append(argv) or completed())
    roothelper._Helper().after_edit("openrc")
    assert calls == []
    roothelper._Helper().after_edit("systemd")
    assert calls == [["systemctl", "--no-ask-password", "daemon-reload"]]


def test_a_masked_unit_has_no_file_to_edit(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", lambda argv: calls.append(argv) or completed("/usr/lib/x.service\n"))
    for masked in (Unit("a.service", startup="masked"), Unit("b.service", load="masked")):
        with pytest.raises(OSError) as refused:
            systemd.unit_file(masked)
        assert "unmask it first" in refused.value.strerror
    assert calls == []


def test_a_package_file_is_overridden_and_the_admins_own_edited(tmp_path, monkeypatch):
    own = tmp_path / "etc"
    (own / "linked.service").parent.mkdir()
    vendor = tmp_path / "usr" / "cron.service"
    vendor.parent.mkdir()
    vendor.write_text("[Service]\nExecStart=/usr/sbin/cron\n")
    (own / "linked.service").symlink_to(vendor)
    (own / "mine.service").write_text("")
    monkeypatch.setattr(systemd, "admin_dir", lambda user: own)
    unit = Unit("cron.service")
    assert systemd.edit_target(unit, vendor) == (own / "cron.service.d" / "override.conf", vendor)
    # A link in /etc to a package's file is still the package's.
    assert systemd.edit_target(unit, own / "linked.service")[1] == own / "linked.service"
    assert systemd.edit_target(unit, own / "mine.service") == (own / "mine.service", None)
    text = systemd.override_text(unit, vendor, vendor.read_text())
    lines = text.splitlines()
    assert all(line.startswith("#") or not line for line in lines)
    assert lines[systemd.OVERRIDE_LINE - 1] == "" and "# ExecStart=/usr/sbin/cron" in lines


def test_the_admins_directories(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert systemd.admin_dir(False) == Path("/etc/systemd/system")
    assert systemd.admin_dir(True) == tmp_path / "systemd" / "user"


def edit_run(tmp_path, monkeypatch, fragment, *after):
    reloads: list[bool] = []
    monkeypatch.setattr(systemd, "admin_dir", lambda user: tmp_path / "etc")
    monkeypatch.setattr(systemd, "unit_file", lambda unit: fragment)
    monkeypatch.setattr(systemd, "daemon_reload", lambda user: reloads.append(user))
    seen = {}

    def editing(a):
        from navigator.widgets.editor.edit_window import EditWindow

        return isinstance(a.shell.desktop.active_window, EditWindow)

    def save(a):
        editor = a.shell.desktop.active_window.editor
        seen["path"], seen["line"] = editor.path, editor.line
        editor.insert_text("# edited\n")
        a.post_event(KeyEvent("f2"))

    service_run(tmp_path, monkeypatch, KeyEvent("f4"), Until(editing), save, Until(lambda a: bool(reloads)))
    assert reloads == [False]
    return seen


def test_f4_edits_the_admins_own_unit_file_and_saving_it_reloads_systemd(tmp_path, monkeypatch):
    fragment = tmp_path / "etc" / "broken.service"
    fragment.parent.mkdir()
    fragment.write_text("[Unit]\nDescription=Broken thing\n")
    seen = edit_run(tmp_path, monkeypatch, fragment)
    assert seen["path"] == fragment
    assert fragment.read_text().startswith("# edited\n[Unit]")


def test_f4_on_a_package_file_writes_a_drop_in_override(tmp_path, monkeypatch):
    vendor = tmp_path / "usr" / "broken.service"
    vendor.parent.mkdir()
    vendor.write_text("[Unit]\nDescription=Broken thing\n")
    seen = edit_run(tmp_path, monkeypatch, vendor)
    override = tmp_path / "etc" / "broken.service.d" / "override.conf"
    assert seen["path"] == override and seen["line"] == systemd.OVERRIDE_LINE - 1
    lines = override.read_text().splitlines()
    assert lines[systemd.OVERRIDE_LINE - 1] == "# edited" and "# Description=Broken thing" in lines
    assert vendor.read_text() == "[Unit]\nDescription=Broken thing\n"


@pytest.mark.parametrize("existed, saved, kept", [(False, False, False), (False, True, True), (True, False, True)])
def test_the_override_directory_made_for_an_unsaved_override_is_removed(tmp_path, monkeypatch, existed, saved, kept):
    vendor = tmp_path / "usr" / "broken.service"
    vendor.parent.mkdir()
    vendor.write_text("[Unit]\nDescription=Broken thing\n")
    directory = tmp_path / "etc" / "broken.service.d"
    if existed:
        directory.mkdir(parents=True)
    monkeypatch.setattr(systemd, "admin_dir", lambda user: tmp_path / "etc")
    monkeypatch.setattr(systemd, "unit_file", lambda unit: vendor)
    monkeypatch.setattr(systemd, "daemon_reload", lambda user: None)
    override = directory / "override.conf"

    def editing(a):
        from navigator.widgets.editor.edit_window import EditWindow

        return isinstance(a.shell.desktop.active_window, EditWindow)

    def close(a):
        # What closing does once *Save?* was answered No (or the text was saved).
        a.shell.desktop.active_window.close()

    steps = [KeyEvent("f4"), Until(editing)]
    if saved:
        steps += [KeyEvent("f2"), Until(lambda a: override.exists())]
    steps += [close, Until(lambda a: not directory.exists() or kept, timeout=5)]
    service_run(tmp_path, monkeypatch, *steps)
    time.sleep(0.2)  # a removal on its thread would be done by now
    assert directory.is_dir() is kept
    assert override.exists() is saved
