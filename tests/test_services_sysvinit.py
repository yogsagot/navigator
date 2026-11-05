"""Utilities > Services with SysVinit: the scripts and their headers, what is never listed, ``status``
run only where it is handled, each verb, the root helper's ownership check, F3 and F4, and the window."""

from __future__ import annotations

import errno
import os
import subprocess

import pytest

from conftest import Until

from navigator.lib.system import services
from navigator.lib.system.services import UNKNOWN, Unit, common, sysvinit

from test_services import service_run


def completed(stdout: str = "", returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


LSB = """#!/bin/sh
### BEGIN INIT INFO
# Provides:          {name}
# Required-Start:    $remote_fs
# Default-Start:     {start}
# Default-Stop:      {stop}
# Short-Description: {short}
# Description:       A longer text
#                    over two lines.
### END INIT INFO
"""

STATUS = """case "$1" in
  start) ;;
  stop) ;;
  status)
    status_of_proc ;;
esac
"""


@pytest.fixture
def etc(tmp_path, monkeypatch):
    """``init.d`` with: cron (LSB, status, reads /etc/default), httpd (Red Hat header, status, reads
    /etc/sysconfig), legacy (no status case), slow (status that never answers), denied (status 4),
    halt (shutdown-only header), sendsigs (hidden by name), README (not executable); ``rc2.d`` and
    ``rcS.d`` links."""
    init_d = tmp_path / "init.d"
    init_d.mkdir()
    default, sysconfig = tmp_path / "default", tmp_path / "sysconfig"
    default.mkdir()
    sysconfig.mkdir()
    scripts = {
        "cron": LSB.format(name="cron", start="2 3 4 5", stop="", short="Regular background program processing")
        + f'[ -r {default}/cron ] && . {default}/cron\nEXTRA_OPTS="-L 1"\n' + STATUS,
        "httpd": "#!/bin/sh\n# chkconfig: 2345 85 15\n# description: The Apache HTTP Server\n"
        + f". {sysconfig}/httpd\n" + STATUS,
        "legacy": "#!/bin/sh\n/usr/sbin/legacyd &\n",
        "slow": LSB.format(name="slow", start="2", stop="", short="Slow") + STATUS,
        "denied": LSB.format(name="denied", start="2", stop="", short="Denied") + STATUS,
        "halt": LSB.format(name="halt", start="", stop="0", short="Execute the halt command") + STATUS,
        "sendsigs": "#!/bin/sh\n" + STATUS,
    }
    for name, text in scripts.items():
        (init_d / name).write_text(text)
        (init_d / name).chmod(0o755)
    (init_d / "README").write_text("not a service\n")
    for level, links in (("2", ["S01cron", "S85httpd", "K01legacy"]), ("S", ["S10slow"]), ("0", ["K01cron"])):
        (tmp_path / f"rc{level}.d").mkdir()
        for link in links:
            (tmp_path / f"rc{level}.d" / link).symlink_to(init_d / link[3:])
    monkeypatch.setattr(sysvinit, "INIT_DIRS", (init_d,))
    monkeypatch.setattr(sysvinit, "RC_BASES", (tmp_path,))
    monkeypatch.setattr(sysvinit, "DEFAULTS", (default, sysconfig))
    monkeypatch.setattr(sysvinit, "LOG_DIR", tmp_path / "log")
    monkeypatch.setattr(common, "SYSTEM_LOGS", (tmp_path / "messages",))
    return tmp_path


def fake_scripts(calls, codes=None):
    codes = {"cron": 0, "httpd": 3, "denied": 4, **(codes or {})}

    def run(argv, timeout=common.TIMEOUT):
        calls.append(argv)
        name = os.path.basename(argv[0])
        if argv[-1] == "status":
            if name == "slow":
                raise OSError(errno.ETIMEDOUT, "slow did not answer in time")
            return completed(returncode=codes.get(name, 0))
        return completed(returncode=codes.get(f"{name} {argv[-1]}", 0), stderr="must be root\n")
    return run


def test_the_scripts_are_listed_with_their_headers_and_runlevels_and_the_dangerous_left_out(etc, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", fake_scripts(calls))
    found = {unit.name: unit for unit in sysvinit.gather()}
    assert set(found) == {"cron", "httpd", "legacy", "slow", "denied"}
    assert found["cron"].description == "Regular background program processing"
    assert found["httpd"].description == "The Apache HTTP Server"
    assert (found["cron"].startup, found["httpd"].startup, found["slow"].startup) == ("2", "2", "boot")
    assert found["legacy"].startup == "disabled"
    assert {unit.backend for unit in found.values()} == {"sysvinit"}


def test_status_is_run_only_where_it_is_handled_and_its_code_read(etc, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", fake_scripts(calls))
    found = {unit.name: (unit.active, unit.sub) for unit in sysvinit.gather()}
    assert found == {"cron": ("running", ""), "httpd": ("stopped", ""), "legacy": ("unknown", "no status action"),
                     "slow": ("unknown", "no answer"), "denied": (UNKNOWN, "")}
    ran = {os.path.basename(argv[0]) for argv in calls}
    assert "legacy" not in ran and "halt" not in ran and "sendsigs" not in ran
    assert all(argv[-1] == "status" for argv in calls)
    monkeypatch.setattr(common, "run", fake_scripts([], {"cron": 1, "httpd": 2}))
    states = sysvinit.states()
    assert states["cron"] == ("fail", "pid file left") and states["httpd"] == ("fail", "lock file left")


def test_actions_run_the_script_and_enabling_needs_a_tool(etc, monkeypatch):
    from navigator.lib.system.elevate import refused

    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", fake_scripts(calls, {"cron stop": 4}))
    monkeypatch.setattr(sysvinit, "enabler", lambda: None)
    assert "enable" not in sysvinit.BACKEND.verbs
    sysvinit.act(Unit("cron", backend="sysvinit"), "restart")
    assert calls == [[str(etc / "init.d" / "cron"), "restart"]]
    with pytest.raises(OSError) as denied:
        services.act(Unit("cron", backend="sysvinit"), "stop")
    assert refused(denied.value)
    for verb, name in (("enable", "cron"), ("start", "halt"), ("start", "nosuch")):
        with pytest.raises(OSError) as invalid:
            sysvinit.act(Unit(name, backend="sysvinit"), verb)
        assert invalid.value.errno == errno.EINVAL
    calls.clear()
    monkeypatch.setattr(sysvinit, "enabler", lambda: "update-rc.d")
    sysvinit.act(Unit("httpd", backend="sysvinit"), "disable")
    sysvinit.act(Unit("slow", backend="sysvinit"), "enable")
    (etc / "rc2.d" / "S01cron").unlink()
    (etc / "rc0.d" / "K01cron").unlink()
    sysvinit.act(Unit("cron", backend="sysvinit"), "enable")
    assert calls == [["update-rc.d", "httpd", "disable"], ["update-rc.d", "slow", "enable"],
                     ["update-rc.d", "cron", "defaults"], ["update-rc.d", "cron", "enable"]]
    calls.clear()
    monkeypatch.setattr(sysvinit, "enabler", lambda: "chkconfig")
    sysvinit.act(Unit("httpd", backend="sysvinit"), "enable")
    sysvinit.act(Unit("httpd", backend="sysvinit"), "disable")
    assert calls == [["chkconfig", "--add", "httpd"], ["chkconfig", "httpd", "on"], ["chkconfig", "httpd", "off"]]


def test_the_helper_runs_only_a_script_root_owns_and_nobody_else_may_write(etc, monkeypatch):
    from navigator.lib.system import roothelper

    calls: list[list[str]] = []
    monkeypatch.setattr(common, "run", fake_scripts(calls))
    helper = roothelper._Helper()
    with pytest.raises(OSError) as owned:
        helper.service("sysvinit", "start", "cron")  # owned by the test's user, not root
    assert owned.value.errno == errno.EINVAL and calls == []
    monkeypatch.setattr(sysvinit, "OWNER", os.getuid())
    helper.service("sysvinit", "start", "cron")
    assert calls == [[str(etc / "init.d" / "cron"), "start"]]
    (etc / "init.d" / "cron").chmod(0o775)
    with pytest.raises(OSError):
        helper.service("sysvinit", "stop", "cron")
    with pytest.raises(OSError):
        helper.service("sysvinit", "start", "halt")
    assert helper.service_states("sysvinit")["httpd"] == ["stopped", ""]


def test_f3_follows_a_log_by_the_name_else_the_system_log_else_says_there_is_none(etc):
    with pytest.raises(OSError) as none:
        services.log(Unit("cron", backend="sysvinit"))
    assert "SysVinit keeps no log for cron" in none.value.strerror
    (etc / "messages").write_text("")
    assert services.log(Unit("cron", backend="sysvinit")) == services.LogFile(etc / "messages", "cron")
    (etc / "log").mkdir()
    (etc / "log" / "cron.log").write_text("")
    assert services.log(Unit("cron", backend="sysvinit")) == services.LogFile(etc / "log" / "cron.log", guessed=True)


def test_f4_edits_the_settings_file_the_script_reads_else_the_script_after_a_warning(etc):
    plan = services.edit_plan(Unit("cron", backend="sysvinit"))
    assert plan.path == etc / "default" / "cron" and plan.line == sysvinit.CONF_LINE
    assert '# EXTRA_OPTS="-L 1"' in plan.seed.splitlines()
    (etc / "sysconfig" / "httpd").write_text("OPTIONS=\n")
    assert services.edit_plan(Unit("httpd", backend="sysvinit")) == services.EditPlan(etc / "sysconfig" / "httpd")
    script = services.edit_plan(Unit("legacy", backend="sysvinit"))
    assert script.path == etc / "init.d" / "legacy" and "may replace it or ask about it" in script.warning


def test_a_long_header_description_and_red_hats_are_read():
    fields = sysvinit.header(LSB.format(name="x", start="2", stop="0", short="Short"))
    assert fields["Description"] == "A longer text over two lines." and fields["Default-Stop"] == "0"
    assert sysvinit.shutdown_only({"Default-Start": "", "Default-Stop": "0 6"})
    assert not sysvinit.shutdown_only({"Default-Start": "2 3", "Default-Stop": "0 6"})
    assert not sysvinit.shutdown_only({})
    assert sysvinit.has_status('  "status")\n') and not sysvinit.has_status("echo status of things\n")


# -- the window --------------------------------------------------------------


def sysv_units() -> list[Unit]:
    return [Unit("cron", "", "running", "", "2, 3, 4, 5", "Cron", False, "sysvinit"),
            Unit("denied", "", UNKNOWN, "", "2", "Denied", False, "sysvinit")]


def test_the_window_reads_sysvinit_no_oftener_than_its_floor_and_greys_enabling_without_a_tool(
        tmp_path, monkeypatch):
    from navkit.application import Application

    from navigator.widgets.shell.commands import EnableService, StartService

    every: list[float] = []
    original = Application.call_every

    def spy(self, seconds, *args, **kwargs):
        every.append(seconds)
        return original(self, seconds, *args, **kwargs)

    monkeypatch.setattr(Application, "call_every", spy)
    monkeypatch.setattr(sysvinit, "refusal", lambda: "")
    monkeypatch.setattr(sysvinit, "enabler", lambda: None)
    seen = {}

    def look(a):
        window = a.shell.desktop.active_window
        seen["title"] = window.title
        seen["status"] = window.status.text
        seen["refusals"] = (window.refusal(EnableService()), window.refusal(StartService()))

    service_run(tmp_path, monkeypatch, Until(lambda a: a.shell.desktop.active_window.status.text), look,
                units=sysv_units, manager="sysvinit", refresh=3)
    assert seen["title"] == "Services (SysVinit)"
    assert 15 in every and 3 not in every
    assert seen["refusals"] == ("Not something SysVinit does", "")
    assert seen["status"].endswith("states need root: Ctrl+R reads them as root")
