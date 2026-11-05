"""Utilities > Services with OpenRC: reading ``rc-status``/``rc-update``, what each verb runs,
F3's log and F4's ``/etc/conf.d`` file, the backend's choice, and the window greying what OpenRC has not."""

from __future__ import annotations

import errno
import subprocess

import pytest

from navkit.events import KeyEvent

from conftest import Until

from navigator.lib.system import services
from navigator.lib.system.services import Unit, common, openrc, systemd

from test_services import service_run


def completed(stdout: str = "", returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


SERVICELIST = """\
 bootmisc                                                          [  started  ]
 crond                                                             [  started  ]
 sshd                                                              [  crashed  ]
 nginx                                                             [  stopped  ]
 networking                                                        [  started 1 day, 02:03:04 (0)]
"""

RUNLEVELS = """\
             bootmisc | boot
                crond |      default
                 sshd |      default
                nginx |
           networking | boot default
"""


@pytest.fixture
def etc(tmp_path, monkeypatch):
    """``/etc/init.d`` and ``/etc/conf.d`` in *tmp_path*, a script for each service."""
    init_d, conf_d = tmp_path / "init.d", tmp_path / "conf.d"
    init_d.mkdir()
    conf_d.mkdir()
    for name in ("bootmisc", "crond", "sshd", "nginx", "networking"):
        (init_d / name).write_text("#!/sbin/openrc-run\n")
    (init_d / "sshd").write_text('#!/sbin/openrc-run\ndescription="OpenBSD Secure Shell server"\n'
                                 'command=/usr/sbin/sshd\ncommand_args="${SSHD_OPTS}"\n'
                                 'pidfile="/run/$RC_SVCNAME.pid"\n\ndepend() {\n\tneed net\n}\n')
    monkeypatch.setattr(openrc, "INIT_D", init_d)
    monkeypatch.setattr(openrc, "CONF_D", conf_d)
    monkeypatch.setattr(openrc, "SYSTEM_LOGS", (tmp_path / "messages",))
    return tmp_path


def fake_rc(calls: list[list[str]], refuse: bool = False):
    def run(argv):
        calls.append(argv)
        if argv[0] == "rc-status":
            return completed(SERVICELIST)
        if argv[:2] == ["rc-update", "show"]:
            return completed(RUNLEVELS)
        if refuse:
            return completed(returncode=1, stderr=" * rc-service: superuser access required\n")
        return completed()
    return run


def test_states_and_runlevels_are_merged_and_the_description_read_from_the_script(etc, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", fake_rc(calls))
    found = {unit.name: unit for unit in openrc.gather()}
    assert set(found) == {"bootmisc", "crond", "sshd", "nginx", "networking"}
    assert found["sshd"].failed and found["sshd"].description == "OpenBSD Secure Shell server"
    assert found["crond"].running and found["crond"].startup == "default"
    # The uptime newer OpenRC prints after the state is not part of it.
    assert found["networking"].active == "started" and found["networking"].startup == "boot, default"
    assert found["nginx"].startup == "disabled" and not found["nginx"].running
    assert {unit.backend for unit in found.values()} == {"openrc"}
    assert calls == [["rc-status", "--servicelist"], ["rc-update", "show", "--verbose"]]


def test_each_verb_runs_rc_service_or_rc_update_and_a_refusal_is_eperm(etc, monkeypatch):
    from navigator.lib.system.elevate import refused

    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", fake_rc(calls))
    for verb in ("start", "stop", "restart", "reload", "enable"):
        openrc.act(Unit("crond", backend="openrc"), verb)
    openrc.act(Unit("networking", backend="openrc"), "disable")
    assert calls == [
        ["rc-service", "crond", "start"], ["rc-service", "crond", "stop"], ["rc-service", "crond", "restart"],
        ["rc-service", "crond", "reload"], ["rc-update", "add", "crond", "default"],
        ["rc-update", "show", "--verbose"],
        ["rc-update", "del", "networking", "boot"], ["rc-update", "del", "networking", "default"],
    ]
    for verb, name in (("mask", "crond"), ("start", "-x"), ("start", "../x")):
        with pytest.raises(OSError) as invalid:
            openrc.act(Unit(name, backend="openrc"), verb)
        assert invalid.value.errno == errno.EINVAL
    monkeypatch.setattr(common, "run", fake_rc(calls, refuse=True))
    with pytest.raises(OSError) as denied:
        services.act(Unit("crond", backend="openrc"), "start")
    assert refused(denied.value) and denied.value.strerror == "rc-service: superuser access required"


def test_details_say_the_status_runlevels_and_script(etc, monkeypatch):
    monkeypatch.setattr(common, "run", lambda argv: completed(returncode=3, stdout=" * status: crashed\n"))
    text = openrc.details(Unit("sshd", active="crashed", startup="default", description="SSH", backend="openrc"))
    assert text.splitlines()[:3] == ["sshd - SSH", "status: crashed", "Runlevels: default"]
    assert str(etc / "init.d" / "sshd") in text


def test_f3_follows_the_services_own_log_else_the_system_log_filtered_else_says_there_is_none(etc):
    unit = Unit("nginx", backend="openrc")
    with pytest.raises(OSError) as none:
        services.log(unit)
    assert none.value.errno == errno.ENOENT
    (etc / "messages").write_text("")
    assert services.log(unit) == services.LogFile(etc / "messages", "nginx")
    own = etc / "nginx.log"
    own.write_text("")
    (etc / "conf.d" / "nginx").write_text(f'output_log="{own}"\n')
    assert services.log(unit) == services.LogFile(own)
    # A path made of variables is not followed: it cannot be known here.
    (etc / "conf.d" / "nginx").write_text('output_log="/var/log/$RC_SVCNAME.log"\n')
    assert services.log(unit).pattern == "nginx"


def test_f4_edits_conf_d_seeded_with_the_scripts_settings(etc):
    unit = Unit("sshd", backend="openrc")
    plan = services.edit_plan(unit)
    assert plan.path == etc / "conf.d" / "sshd" and plan.line == openrc.CONF_LINE
    lines = plan.seed.splitlines()
    assert all(line.startswith("#") or not line for line in lines)
    assert lines[plan.line - 1] == ""
    assert "# command=/usr/sbin/sshd" in lines and '# pidfile="/run/$RC_SVCNAME.pid"' in lines
    assert not any("need net" in line or "depend" in line for line in lines)
    plan.path.write_text("SSHD_OPTS=-4\n")
    assert services.edit_plan(unit) == services.EditPlan(plan.path)


def test_the_running_manager_is_picked_unless_one_is_named(monkeypatch):
    from navigator.settings import SETTINGS

    monkeypatch.setattr(SETTINGS.services, "manager", "auto")
    monkeypatch.setattr(systemd, "refusal", lambda: "no systemd")
    monkeypatch.setattr(openrc, "refusal", lambda: "")
    assert services.current() is openrc.BACKEND and services.refusal_reason() == ""
    monkeypatch.setattr(openrc, "refusal", lambda: "no openrc")
    assert services.current() is None
    assert "systemd or OpenRC" in services.refusal_reason()
    monkeypatch.setattr(SETTINGS.services, "manager", "systemd")
    assert services.current() is systemd.BACKEND and services.refusal_reason() == "no systemd"


def test_the_helper_acts_only_on_a_script_that_is_there(etc, monkeypatch):
    from navigator.lib.system import roothelper

    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", fake_rc(calls))
    helper = roothelper._Helper()
    with pytest.raises(OSError) as missing:
        helper.service("openrc", "start", "nosuch")
    assert missing.value.errno == errno.EINVAL and calls == []
    helper.service("openrc", "enable", "crond")
    assert calls == [["rc-update", "add", "crond", "default"]]


# -- the window --------------------------------------------------------------


def openrc_units() -> list[Unit]:
    return [
        Unit("crond", "", "started", "", "default", "Cron daemon", False, "openrc"),
        Unit("nginx", "", "stopped", "", "disabled", "", False, "openrc"),
        Unit("sshd", "", "crashed", "", "default", "OpenBSD Secure Shell server", False, "openrc"),
    ]


def openrc_run(where, monkeypatch, *actions, reads=None):
    # This machine need not run OpenRC: the shell would grey Services.
    monkeypatch.setattr(openrc, "refusal", lambda: "")
    return service_run(where, monkeypatch, *actions, reads=reads, units=openrc_units, manager="openrc")


def test_the_window_names_openrc_and_greys_what_it_has_not(tmp_path, monkeypatch):
    from navigator.widgets.shell.commands import MaskService, ServiceAllTypes, ServiceUserUnits, StartService

    seen = {}
    reads: list[tuple[bool, bool]] = []

    def look(a):
        window = a.shell.desktop.active_window
        seen["title"] = window.title
        seen["first"] = window.units.titles()[0]
        seen["boxes"] = (window.user_box.disabled, window.types_box.disabled)
        seen["refusals"] = [window.refusal(command()) for command in
                            (MaskService, ServiceUserUnits, ServiceAllTypes, StartService)]

    openrc_run(tmp_path, monkeypatch, look, KeyEvent("u", ctrl=True), KeyEvent("m", ctrl=True), reads=reads)
    assert seen["title"] == "Services (OpenRC)" and seen["first"] == "Service"
    assert seen["boxes"] == (True, True)
    assert seen["refusals"][:3] == ["Not something OpenRC does"] * 3 and seen["refusals"][3] == ""
    assert reads == [(False, False)]


def test_a_refused_start_goes_to_the_helpers_service_op_for_openrc(tmp_path, monkeypatch):
    from navigator.lib.system import elevate
    from navigator.widgets.file_ops import as_root

    root_calls = []

    def refuse(unit, verb):
        raise PermissionError(errno.EPERM, "rc-service: superuser access required")

    async def yes(app, message, **kwargs):
        return True

    original = elevate.ELEVATION.call

    def call(op, payload=b"", **args):
        if op != "service":
            return original(op, payload, **args)
        root_calls.append(args)

    monkeypatch.setattr(services, "act", refuse)
    monkeypatch.setattr(elevate.ELEVATION, "available", lambda: True)
    monkeypatch.setattr(elevate.ELEVATION, "call", call)
    monkeypatch.setattr(elevate.ELEVATION, "release", lambda: None)
    monkeypatch.setattr(as_root, "ask_as_root", yes)
    openrc_run(tmp_path, monkeypatch, KeyEvent("f5"), Until(lambda a: bool(root_calls)))
    assert root_calls == [{"manager": "openrc", "verb": "start", "unit": "crond"}]


def test_f3_follows_the_system_log_showing_only_the_services_lines(etc, monkeypatch):
    from navigator.widgets.viewer.file_window import FileWindow

    (etc / "messages").write_text("Nov  5 10:00:00 host crond[12]: started\n"
                                  "Nov  5 10:00:01 host sshd[13]: listening\n"
                                  "Nov  5 10:00:02 host crond[12]: job ran\n")
    seen = {}

    def viewing(a):
        window = a.shell.desktop.active_window
        return isinstance(window, FileWindow) and window.viewer.follow and window.viewer.lines is not None

    def look(a):
        window = a.shell.desktop.active_window
        seen["title"] = window.title
        seen["pattern"] = window.viewer.lines.pattern.text

    openrc_run(etc, monkeypatch, KeyEvent("f3"), Until(viewing, timeout=10), look)
    assert seen["pattern"] == "crond"
    assert seen["title"] == f"Log: crond (its lines in {etc / 'messages'})"


def test_f4_edits_conf_d_and_saving_it_offers_a_restart_of_a_running_service(etc, monkeypatch):
    from navigator.widgets.editor.edit_window import EditWindow

    (etc / "init.d" / "crond").write_text('#!/sbin/openrc-run\ncommand=/usr/sbin/crond\n')
    done: list[tuple[str, str]] = []
    monkeypatch.setattr(services, "act", lambda unit, verb: done.append((unit.name, verb)))
    seen = {}

    def editing(a):
        return isinstance(a.shell.desktop.active_window, EditWindow)

    def save(a):
        editor = a.shell.desktop.active_window.editor
        seen["path"] = editor.path
        editor.insert_text("CRON_OPTS=-l 2\n")
        a.post_event(KeyEvent("f2"))

    openrc_run(etc, monkeypatch, KeyEvent("f4"), Until(editing), save,
               Until(lambda a: a.modal is not None and "Restart" in str(getattr(a.modal, "prompt", ""))),
               KeyEvent("enter"), Until(lambda a: bool(done)))
    conf = etc / "conf.d" / "crond"
    assert seen["path"] == conf
    lines = conf.read_text().splitlines()
    assert lines[openrc.CONF_LINE - 1] == "CRON_OPTS=-l 2" and "# command=/usr/sbin/crond" in lines
    assert done == [("crond", "restart")]
