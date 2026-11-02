"""Operations sent to the background: the boxes' *Background*, the bar's mark, the toast."""

from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path

import pytest

from conftest import FakeTerminal

from navkit.application import Application
from navkit.events import KeyEvent, MouseClickEvent

from navml.widgets.toast import Toast

from navigator.lib.file_ops import fileerase
from navigator.lib.system.background import BACKGROUND
from navigator.widgets.file_ops.background_button import BACKGROUND as AWAY
from navigator.widgets.file_ops.copy_progress import CopyProgress
from navigator.widgets.file_ops.delete_progress import DeleteProgress
from navigator.widgets.shell.commands import ShowBackground
from navigator.widgets.shell.job_mark import caption
from navigator.widgets.shell.shell import Shell


@pytest.fixture
def two(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "one.txt").write_text("one")
    return a, b


def run_shell(a: Path, b: Path, steps):
    async def main():
        shell = Shell(a, b)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        BACKGROUND.listener = app.invalidate
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.1)
        try:
            return await steps(app, shell)
        finally:
            app.exit()
            await task

    return asyncio.run(main())


async def wait_for(predicate, timeout: float = 2.0) -> None:
    end = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > end:
            raise AssertionError("timed out")
        await asyncio.sleep(0.02)


def put_cursor(panel, name: str) -> None:
    panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == name)


def toasts(shell) -> list[Toast]:
    return [child for child in shell.children if isinstance(child, Toast)]


def held_erase(monkeypatch, release: threading.Event, question=None, answers=None, ask_now=None):
    """``fileerase.run`` replaced by one half done until *release*, asking
    *question* first if given, once *ask_now* is set."""

    def slow(request, job):
        job.total, job.measuring = 10, False
        job.action, job.path = fileerase.ERASING_FILE, str(request.sources[0])
        job.done = 4
        if question is not None:
            ask_now.wait(5)
            answers.append(job.ask(question))
        while not job.stopped and not release.is_set():
            job.wait_while_paused()
            time.sleep(0.01)
        job.done = 10
        return []

    monkeypatch.setattr(fileerase, "run", slow)


# -- the boxes -----------------------------------------------------------------------


@pytest.mark.parametrize("box_class, stop", [(CopyProgress, "~S~top"), (DeleteProgress, "~C~ancel")])
def test_a_box_has_background_only_when_its_watcher_can_let_it_go(box_class, stop):
    box = box_class()
    assert box.ok.text == stop and not box.no.visible
    assert box.accept() is None
    box.background = True
    assert [b.text for b in box.buttons_row if b.visible] == ["~B~ackground", stop]
    assert box.ok.default
    assert box.accept() is AWAY


# -- the registry --------------------------------------------------------------------


def test_the_subject_names_what_was_started():
    from navigator.widgets.manager.manager.manager import job_subject

    one, two = [Path("/home/u/photos")], [Path("/home/u/a"), Path("/home/u/b")]
    assert job_subject("copy", one, "/mnt/backup/") == "Copy photos to /mnt/backup"
    assert job_subject("move", two, "/mnt/backup") == "Move 2 files to /mnt/backup"
    assert job_subject("erase", one) == "Erase photos"
    assert job_subject("erase", two) == "Erase 2 files"
    assert job_subject("copy", [], "/x") == ""
    # The root is still a target.
    assert job_subject("copy", one, "/") == "Copy photos to /"


def test_the_file_in_hand_is_named_from_where_the_sources_are():
    from navigator.widgets.manager.manager.manager import relative_to, source_base

    base = source_base([Path("/home/u/photos")])
    assert base == "/home/u"
    assert relative_to("/home/u/photos/2019/a.jpg", base) == "photos/2019/a.jpg"
    assert relative_to("/elsewhere/a.jpg", base) == "/elsewhere/a.jpg"
    assert relative_to("/home/user2/a.jpg", base) == "/home/user2/a.jpg"
    assert relative_to("/a", "") == "/a"


def test_the_mark_counts_and_flags_a_question():
    assert caption() == ""

    class Job:
        stopped = False

        def stop(self):
            self.stopped = True

    first = BACKGROUND.add(Job(), "Copy")
    first.done, first.total = 50, 100
    assert caption() == " 50% "
    second = BACKGROUND.add(Job(), "Erase")
    second.done, second.total = 1, 10
    assert caption() == " 50%|10% "
    second.asking = True
    assert caption() == " 50%|?10% "
    BACKGROUND.recall()
    assert second.recalled.is_set() and not first.recalled.is_set()
    BACKGROUND.stop_all()
    assert first.job.stopped and second.job.stopped
    BACKGROUND.remove(first)
    BACKGROUND.remove(second)
    assert caption() == ""


def test_each_segment_has_its_own_click_and_tooltip(two):
    a, b = two
    jobs = []

    async def steps(app, shell):
        for title, done in (("Copy", 10), ("Erase", 2)):
            entry = BACKGROUND.add(object(), title)
            entry.done, entry.total = done, 10 if title == "Erase" else 100
            jobs.append(entry)
        await asyncio.sleep(0.05)
        mark = shell.job_mark
        # " 10%|20% ": the first segment and the space before it, then the
        # separator with the second, and the space after it.
        owners = [mark.entry_at(x) for x in range(mark.width)]
        tips = (mark.tooltip_at(1, 0), mark.tooltip_at(6, 0))
        await mark.on_mouse_click(MouseClickEvent(6, 0, button="left"))
        recalled = [entry.recalled.is_set() for entry in jobs]
        return mark.width, owners, tips, recalled

    width, owners, (first, second), recalled = run_shell(a, b, steps)
    assert width == len(" 10%|20% ")
    assert owners == [jobs[0]] * 4 + [jobs[1]] * 5
    assert first.splitlines()[0] == "Copy: 10% done"
    assert second.splitlines()[0] == "Erase: 20% done"
    assert recalled == [False, True]


# -- end to end ----------------------------------------------------------------------


def test_background_takes_the_box_down_and_the_end_is_toasted(two, monkeypatch):
    a, b = two
    release = threading.Event()
    held_erase(monkeypatch, release)

    async def steps(app, shell):
        strip_x = shell.window_strip.x
        put_cursor(shell.manager.left, "one.txt")
        app.post_event(KeyEvent("f8"))
        await asyncio.sleep(0.06)
        app.post_event(KeyEvent("enter"))
        await wait_for(lambda: isinstance(app.modal, DeleteProgress))
        app.post_event(KeyEvent("enter"))
        await wait_for(lambda: bool(BACKGROUND.jobs))
        await asyncio.sleep(0.2)
        seen = {
            "modal": app.modal,
            "visible": shell.job_mark.visible,
            "caption": caption(),
            "strip": shell.window_strip.x - strip_x,
            "mark": shell.job_mark.width,
            # One window: no chips, so the mark keeps to the strip's end.
            "end": (shell.job_mark.x + shell.job_mark.width, shell.window_strip.x + shell.window_strip.width),
            "title": BACKGROUND.jobs[0].title,
            "tip": shell.job_mark.tooltip_at(1, 0).splitlines()[:2],
        }
        release.set()
        await wait_for(lambda: not BACKGROUND.jobs)
        await wait_for(lambda: bool(toasts(shell)))
        toast = toasts(shell)[0]
        seen["toast"] = (toast.title, toast.text)
        seen["after"] = shell.job_mark.visible
        return seen

    seen = run_shell(a, b, steps)
    assert seen["modal"] is None and seen["visible"]
    assert seen["caption"] == " 40% " and seen["title"] == "Erase"
    assert seen["tip"] == ["Erase one.txt: 40% done", "  one.txt"]
    assert seen["strip"] == seen["mark"] == len(" 40% ")
    assert seen["end"][0] == seen["end"][1]
    assert seen["toast"] == ("Erase", "Finished")
    assert not seen["after"]


def test_a_question_waits_in_the_background_until_the_box_is_back(two, monkeypatch):
    a, b = two
    release = threading.Event()
    answers: list = []
    asked: list = []
    ask_now = threading.Event()
    held_erase(monkeypatch, release, question="is it?", answers=answers, ask_now=ask_now)

    async def steps(app, shell):
        manager = shell.manager

        async def answer(question, *, quiet=False):
            asked.append(question)
            return "yes"

        manager._answer_erase_question = answer
        put_cursor(manager.left, "one.txt")
        app.post_event(KeyEvent("f8"))
        await asyncio.sleep(0.06)
        app.post_event(KeyEvent("enter"))
        await wait_for(lambda: isinstance(app.modal, DeleteProgress))
        app.post_event(KeyEvent("enter"))
        await wait_for(lambda: bool(BACKGROUND.jobs))
        ask_now.set()
        await wait_for(lambda: BACKGROUND.asking)
        waiting = (app.modal, list(asked), caption().startswith(" ?"))
        await app.run_command(ShowBackground)
        await wait_for(lambda: bool(asked))
        await wait_for(lambda: isinstance(app.modal, DeleteProgress))
        back = (BACKGROUND.jobs, answers)
        release.set()
        await wait_for(lambda: app.modal is None)
        return waiting, back

    waiting, back = run_shell(a, b, steps)
    assert waiting == (None, [], True)
    assert back == ((), ["yes"])
    assert asked == ["is it?"]


def test_a_click_on_a_toast_takes_it_away(two):
    a, b = two

    async def steps(app, shell):
        first = shell.toast("one", title="Copy")
        second = shell.toast("two", title="Erase")
        await asyncio.sleep(0.05)
        stacked = (first.y, second.y, second.x + second.width)
        await second.on_mouse_click(MouseClickEvent(0, 0, button="left"))
        await asyncio.sleep(0.05)
        return stacked, toasts(shell), first.y

    (first_y, second_y, right), left, moved = run_shell(a, b, steps)
    assert second_y == first_y + 3
    assert right == 79
    assert [t.text for t in left] == ["one"]
    assert moved == second_y


def test_a_toast_goes_by_itself(two):
    a, b = two

    async def steps(app, shell):
        toast = shell.toast("gone soon", seconds=0.1)
        await asyncio.sleep(0.02)
        here = toast in toasts(shell)
        await wait_for(lambda: toast not in toasts(shell))
        return here

    assert run_shell(a, b, steps)


def test_quitting_with_work_in_the_background_asks_and_stops_it(two, monkeypatch):
    from navigator.__main__ import Navigator
    from navigator.commands import Quit

    a, b = two
    stopped = threading.Event()

    def slow(request, job):
        job.total, job.measuring = 10, False
        job.action, job.path = fileerase.ERASING_FILE, str(request.sources[0])
        while not job.stopped:
            job.wait_while_paused()
            time.sleep(0.01)
        stopped.set()
        return []

    monkeypatch.setattr(fileerase, "run", slow)

    async def main():
        app = Navigator(a, b, terminal=FakeTerminal(80, 24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.2)
        try:
            put_cursor(app.shell.manager.left, "one.txt")
            app.post_event(KeyEvent("f8"))
            await asyncio.sleep(0.06)
            app.post_event(KeyEvent("enter"))
            await wait_for(lambda: isinstance(app.modal, DeleteProgress))
            app.post_event(KeyEvent("enter"))
            await wait_for(lambda: bool(BACKGROUND.jobs))
            await app.run_command(Quit)
            await wait_for(lambda: app.modal is not None)
            prompt = app.modal.prompt
            app.post_event(KeyEvent("enter"))
            await asyncio.wait_for(task, 3)
            return prompt
        finally:
            if not task.done():
                app.exit()
                await task

    prompt = asyncio.run(main())
    assert prompt == "1 operation is running in the background. Stop it and quit?"
    assert stopped.wait(2)
