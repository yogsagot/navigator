"""Utilities > Services with runit: definitions and links, ``sv status`` and its refusal, what each
verb does, F3's ``svlogd`` or system log, F4's ``conf`` or ``run``, the helper's ops, and the window
reading states as root."""

from __future__ import annotations

import errno
import os
import subprocess

import pytest

from navkit.events import KeyEvent

from conftest import Until

from navigator.lib.system import services
from navigator.lib.system.services import UNKNOWN, Unit, common, runit

from test_services import service_run


def completed(stdout: str = "", returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """Definitions in ``sv/``, the supervised directory ``service/``: sshd and
    crond enabled (crond with a ``down`` file), nginx and ntpd not, and a
    directory placed in ``service/`` itself."""
    defined, supervised = tmp_path / "sv", tmp_path / "service"
    for name, run, logger in (
        ("sshd", "#!/bin/sh\nexec 2>&1\nexec /usr/bin/sshd -D\n", "#!/bin/sh\nexec svlogd -tt /var/log/sshd\n"),
        ("crond", "#!/bin/sh\n[ -r conf ] && . ./conf\nexec crond -f $OPTS\n", "#!/bin/sh\nexec vlogger -t crond\n"),
        ("nginx", "#!/bin/sh\nexec nginx -g 'daemon off;'\n", None),
        ("ntpd", "#!/bin/sh\nexec ntpd -n\n", None),
    ):
        (defined / name).mkdir(parents=True)
        (defined / name / "run").write_text(run)
        if logger:
            (defined / name / "log").mkdir()
            (defined / name / "log" / "run").write_text(logger)
    supervised.mkdir()
    (supervised / "sshd").symlink_to(defined / "sshd")
    (supervised / "crond").symlink_to(defined / "crond")
    (defined / "crond" / "down").write_text("")
    (supervised / "local").mkdir()
    (supervised / "local" / "run").write_text("#!/bin/sh\nexec local-thing\n")
    monkeypatch.setattr(runit, "DEFINITION_DIRS", (defined,))
    monkeypatch.setattr(runit, "SERVICE_DIRS", (supervised,))
    monkeypatch.delenv("SVDIR", raising=False)
    monkeypatch.setattr(common, "SYSTEM_LOGS", (tmp_path / "messages",))
    return tmp_path


def status_of(supervised) -> str:
    return (f"run: {supervised}/crond: (pid 12) 3600s; run: log: (pid 11) 3600s\n"
            f"run: {supervised}/local: (pid 14) 5s\n"
            f"down: {supervised}/sshd: 40s, normally up; run: log: (pid 13) 3600s\n")


REFUSED = ("warning: {0}/crond: unable to open supervise/ok: access denied\n"
           "warning: {0}/local: unable to open supervise/ok: access denied\n"
           "warning: {0}/sshd: unable to open supervise/ok: access denied\n")


def fake_sv(calls, supervised, refuse=False):
    def run(argv):
        calls.append(argv)
        if argv[:2] == ["sv", "status"]:
            return completed(REFUSED.format(supervised) if refuse else status_of(supervised), returncode=1 if refuse else 0)
        if refuse:
            return completed(returncode=1, stderr=REFUSED.format(supervised).splitlines()[0])
        return completed()
    return run


def test_status_lines_are_read_and_a_refusal_told_apart_from_a_missing_supervisor():
    found, refused = runit.parse_status(
        "run: /var/service/sshd: (pid 9) 120s; run: log: (pid 8) 120s\n"
        "down: /var/service/ntpd: 5s, normally up\n"
        "warning: /var/service/new: unable to open supervise/ok: file does not exist\n"
        "warning: /var/service/x: unable to open supervise/ok: access denied\n")
    assert found == {"sshd": ("run", "120s"), "ntpd": ("down", "normally up"), "new": ("fail", "")}
    assert refused


def test_definitions_and_links_are_merged_with_the_states(tree, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", fake_sv(calls, tree / "service"))
    found = {unit.name: unit for unit in runit.gather()}
    assert set(found) == {"sshd", "crond", "nginx", "ntpd", "local"}
    assert (found["crond"].active, found["crond"].startup) == ("run", "enabled, down") and found["crond"].running
    assert (found["sshd"].active, found["sshd"].sub, found["sshd"].startup) == ("down", "normally up", "enabled")
    assert (found["nginx"].active, found["nginx"].startup) == ("down", "disabled")
    assert found["sshd"].description == "/usr/bin/sshd -D" and found["local"].description == "local-thing"
    assert {unit.backend for unit in found.values()} == {"runit"}
    assert calls == [["sv", "status", *(str(tree / "service" / name) for name in ("crond", "local", "sshd"))]]


def test_states_the_user_may_not_read_are_unknown_and_the_disabled_still_down(tree, monkeypatch):
    monkeypatch.setattr(common, "run", fake_sv([], tree / "service", refuse=True))
    found = {unit.name: unit for unit in runit.gather()}
    assert {name for name, unit in found.items() if unit.active == UNKNOWN} == {"sshd", "crond", "local"}
    assert found["nginx"].active == "down" and not found["sshd"].running and not found["sshd"].failed
    with pytest.raises(OSError) as refused:
        runit.states()
    assert refused.value.errno == errno.EPERM
    filled = common.with_states(list(found.values()), {"sshd": ("run", "9s")})
    assert next(unit for unit in filled if unit.name == "sshd").active == "run"


def test_verbs_run_sv_or_change_the_link_and_never_remove_a_directory(tree, monkeypatch):
    from navigator.lib.system.elevate import refused

    calls: list[list[str]] = []
    supervised = tree / "service"
    monkeypatch.setattr(common, "run", fake_sv(calls, supervised))
    for verb in ("start", "stop", "restart", "reload"):
        runit.act(Unit("sshd", backend="runit"), verb)
    assert calls == [["sv", "-w", "7", verb, str(supervised / "sshd")] for verb in ("start", "stop", "restart", "reload")]
    runit.act(Unit("nginx", backend="runit"), "enable")
    assert os.readlink(supervised / "nginx") == str(tree / "sv" / "nginx")
    runit.act(Unit("sshd", backend="runit"), "disable")
    assert not os.path.lexists(supervised / "sshd")
    with pytest.raises(OSError) as directory:
        runit.act(Unit("local", backend="runit"), "disable")
    assert directory.value.errno == errno.EINVAL and (supervised / "local" / "run").exists()
    with pytest.raises(OSError) as disabled:
        runit.act(Unit("ntpd", backend="runit"), "start")
    assert "enable it first" in disabled.value.strerror
    monkeypatch.setattr(common, "run", fake_sv([], supervised, refuse=True))
    with pytest.raises(OSError) as denied:
        services.act(Unit("crond", backend="runit"), "restart")
    assert refused(denied.value)


def test_f3_follows_svlogd_else_the_system_log_filtered_else_says_there_is_none(tree):
    assert services.log(Unit("sshd", backend="runit")) == services.LogFile(runit.Path("/var/log/sshd/current"))
    with pytest.raises(OSError) as none:
        services.log(Unit("crond", backend="runit"))
    assert none.value.errno == errno.ENOENT and "runit keeps no log for crond" in none.value.strerror
    (tree / "messages").write_text("")
    assert services.log(Unit("crond", backend="runit")) == services.LogFile(tree / "messages", "crond")
    assert runit.svlogd_dir('exec chpst -u log svlogd -tt -r "x" /var/log/a /var/log/b\n') == runit.Path("/var/log/b")


def test_f4_edits_conf_when_run_reads_it_else_run_after_a_warning(tree):
    plan = services.edit_plan(Unit("crond", backend="runit"))
    assert plan.path == tree / "sv" / "crond" / "conf" and plan.line == runit.CONF_LINE and not plan.warning
    assert "# exec crond -f $OPTS" in plan.seed.splitlines()
    plan.path.write_text("OPTS=-l 2\n")
    assert services.edit_plan(Unit("crond", backend="runit")) == services.EditPlan(plan.path)
    run = services.edit_plan(Unit("ntpd", backend="runit"))
    assert run.path == tree / "sv" / "ntpd" / "run" and run.seed is None and "may replace it" in run.warning


def test_the_helpers_ops_for_runit(tree, monkeypatch):
    from navigator.lib.system import roothelper

    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", fake_sv(calls, tree / "service"))
    helper = roothelper._Helper()
    assert helper.service_states("runit") == {"crond": ["run", "3600s"], "local": ["run", "5s"],
                                              "sshd": ["down", "normally up"]}
    with pytest.raises(OSError) as everyones:
        helper.service_states("systemd")
    assert everyones.value.errno == errno.EINVAL
    with pytest.raises(OSError) as missing:
        helper.service("runit", "enable", "nosuch")
    assert missing.value.errno == errno.EINVAL
    helper.service("runit", "enable", "ntpd")
    assert os.path.islink(tree / "service" / "ntpd")


# -- the window --------------------------------------------------------------


def runit_units() -> list[Unit]:
    return [
        Unit("crond", "", UNKNOWN, "", "enabled", "crond -f", False, "runit"),
        Unit("nginx", "", "down", "", "disabled", "nginx", False, "runit"),
        Unit("sshd", "", UNKNOWN, "", "enabled", "/usr/bin/sshd -D", False, "runit"),
    ]


def runit_run(where, monkeypatch, *actions):
    monkeypatch.setattr(runit, "refusal", lambda: "")
    return service_run(where, monkeypatch, *actions, units=runit_units, manager="runit")


#: A reload is read on a thread: done once its answer is in and painted.
READ = Until(lambda a: not a.shell.desktop.active_window._reading and not a.busy)


def test_unknown_states_are_said_and_read_as_root_when_root_access_is_open(tmp_path, monkeypatch):
    from navigator.lib.system import elevate

    root_calls = []
    running = {"open": False}
    monkeypatch.setattr(type(elevate.ELEVATION), "running", property(lambda self: running["open"]))
    monkeypatch.setattr(elevate.ELEVATION, "release", lambda: None)

    original = elevate.ELEVATION.call

    def call(op, payload=b"", **args):
        # A root drive another test left mounted asks for its listing: not ours.
        if op != "service_states":
            return original(op, payload, **args)
        root_calls.append((op, args))
        return {"crond": ["run", "60s"], "sshd": ["fail", ""]}

    monkeypatch.setattr(elevate.ELEVATION, "call", call)
    seen = []

    def look(a):
        window = a.shell.desktop.active_window
        seen.append(([unit.active for unit in window.units.items], window.status.text))

    def open_root(a):
        running["open"] = True

    runit_run(tmp_path, monkeypatch, look, open_root, KeyEvent("r", ctrl=True), Until(lambda a: bool(root_calls)),
              READ, look, lambda a: a.shell.desktop.active_window.reload(explicit=False), READ,
              look)
    assert seen[0][0] == [UNKNOWN, "down", UNKNOWN]
    assert seen[0][1].endswith("states need root: Ctrl+R reads them as root")
    assert root_calls == [("service_states", {"manager": "runit"})]
    assert seen[1][0] == ["run", "down", "fail"] and "root" not in seen[1][1]
    # The timer's read never asks the helper: the states last read as root, said so.
    assert seen[2][0] == ["run", "down", "fail"] and "states read as root at" in seen[2][1]
    assert len(root_calls) == 1


def test_ctrl_r_asks_for_root_when_it_is_not_open(tmp_path, monkeypatch):
    from navigator.lib.system import elevate
    from navigator.widgets.file_ops import as_root

    asked = []

    async def no(app, message, **kwargs):
        asked.append(message)
        return False

    monkeypatch.setattr(elevate.ELEVATION, "available", lambda: True)
    monkeypatch.setattr(as_root, "ask_as_root", no)
    runit_run(tmp_path, monkeypatch, KeyEvent("r", ctrl=True), Until(lambda a: bool(asked)))
    assert "runit" in asked[0]


def test_f4_on_a_service_without_conf_warns_before_editing_its_run_script(tree, monkeypatch):
    from navigator.widgets.editor.edit_window import EditWindow

    seen = {}

    def to_ntpd(a):
        window = a.shell.desktop.active_window
        window.units.cursor = [unit.name for unit in window.units.items].index("ntpd")

    def look(a):
        seen["prompt"] = str(getattr(a.modal, "prompt", ""))

    def editing(a):
        window = a.shell.desktop.active_window
        if isinstance(window, EditWindow):
            seen["path"] = window.editor.path
            return True
        return False

    units = lambda: [*runit_units(), Unit("ntpd", "", "down", "", "disabled", "ntpd -n", False, "runit")]  # noqa: E731
    monkeypatch.setattr(runit, "refusal", lambda: "")
    service_run(tree, monkeypatch, to_ntpd, KeyEvent("f4"), Until(lambda a: a.modal is not None), look,
                KeyEvent("enter"), Until(editing), units=units, manager="runit")
    assert "may replace it" in seen["prompt"]
    assert seen["path"] == tree / "sv" / "ntpd" / "run"
