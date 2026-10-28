"""The handlers behind ``diff_window.nml``, and :func:`open_diff`, which opens one.

The two files are read and aligned on a thread
(:func:`navigator.lib.file_ops.filediff.compare`), under *Comparing files*
if it takes a while, whose Cancel stops it.  Two files that are the same, or
two that are not text (or too large to be aligned), are answered with a box
rather than a window: there is nothing to put side by side.
"""

from __future__ import annotations

from typing import Any

from navkit.events import ContextMenuEvent
from navkit.i18n import tr
from navml.commands import CloseWindow
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.scroll_bar import ScrollEvent
from navml.widgets.menu.commands import ShowContextMenu
from navml.widgets.menu.context_menu import ContextMenu
from navml.widgets.menu.context_menu.context_menu import open_on_click, open_on_key
from navml.widgets.window import Window

from navigator.lib.file_ops import filediff
from navigator.lib.system.job import Stopped
from navigator.widgets.manager.commands import Rescan
from navigator.widgets.viewer.commands import CloseViewer, NextDifference, PreviousDifference


class DiffWindow(Window):
    """Two files side by side: File > Compare files."""

    def __init__(self, left: Any = None, right: Any = None, *, model: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.left_path = left
        self.right_path = right
        self.view.left_title = str(left)
        self.view.right_title = str(right)
        self.view.model = model
        self.title = tr("Compare {left} with {right}").format(left=_name(left), right=_name(right))

    def take_keyboard(self) -> None:
        self.view.focus()

    def list_name(self) -> str:
        """Window > List's line."""
        return tr("Compare - {left}, {right}").format(left=self.left_path, right=self.right_path)

    def short_name(self) -> str:
        return f"{_name(self.left_path)} | {_name(self.right_path)}"

    # -- the commands --------------------------------------------------------------

    async def on_next_difference(self, event: NextDifference) -> bool:
        if not self.view.next_difference() and self.application is not None:
            self.application.bell()
        return True

    async def on_previous_difference(self, event: PreviousDifference) -> bool:
        if not self.view.previous_difference() and self.application is not None:
            self.application.bell()
        return True

    async def on_close_viewer(self, event: CloseViewer) -> bool:
        self.request_close()
        return True

    async def on_rescan(self, event: Rescan) -> bool:
        self.spawn(self.compare_again())
        return True

    async def compare_again(self) -> None:
        """Ctrl+R: the two files read and aligned again, the view kept where it was."""
        result = await compare_files(self.application, self.left_path, self.right_path)
        if result is None:
            return
        view = self.view
        if not isinstance(result, filediff.TextDiff):
            await say_result(self.application, result)
            return
        top = view.top
        view.model = result
        view.current = -1
        view.scroll_to(top)

    def refusal(self, command: Any) -> str:
        """Next and Previous want a difference to go to."""
        if isinstance(command, (NextDifference, PreviousDifference)):
            model = self.view.model
            return "" if model is not None and model.hunks else tr("The files do not differ")
        return super().refusal(command)

    async def on_bar_scroll(self, event: ScrollEvent) -> bool:
        self.view.scroll_to(event.value)
        return True

    # -- the right-click menu: ``ContextMenuHost``'s hooks, written out, as
    # ``VolumesWindow``'s are.

    def context_menu(self) -> ContextMenu:
        """The *Compare* menu's entries, built each time so its captions follow the language."""
        menu = ContextMenu()
        menu.add_item(tr("~N~ext difference"), NextDifference)
        menu.add_item(tr("~P~revious difference"), PreviousDifference)
        menu.add_line()
        menu.add_item(tr("~C~ompare again"), Rescan)
        menu.add_line()
        menu.add_item(tr("C~l~ose"), CloseWindow)
        return menu

    def prepare_context(self, x: int, y: int) -> None:
        """Nothing to point at: the menu acts on the whole view."""

    def context_point(self) -> tuple[int, int]:
        return self.view.x + 2, self.view.y + 2

    async def on_context_menu(self, event: ContextMenuEvent) -> bool:
        return open_on_click(self, event)

    async def on_show_context_menu(self, command: ShowContextMenu) -> bool:
        return open_on_key(self)


def _name(place: Any) -> str:
    return getattr(place, "name", "") or str(place)


async def compare_files(app: Any, left: Any, right: Any) -> Any:
    """``filediff.compare`` on a thread, under *Comparing files* if it takes
    a while; None when cancelled, or when a file could not be read (said)."""
    from navigator.lib.file_ops.filecopy import error_message
    from navigator.lib.system.progress import SLOW_PROGRESS_DELAY, run_with_progress
    from navigator.widgets.editor.loading import progress_box, refresh_box

    job = filediff.DiffJob()
    try:
        return await run_with_progress(
            app, lambda: filediff.compare(left, right, job), job,
            lambda: progress_box(job, tr("Comparing files")), refresh_box(job),
            delay=SLOW_PROGRESS_DELAY,
        )
    except Stopped:
        return None
    except OSError as error:
        if app is not None:
            await Dialog(title=tr("Error"), prompt=escape_caption(error_message(error)), buttons="ok").execute(app)
        return None


async def say_result(app: Any, result: Any) -> None:
    """A comparison with nothing to show side by side, said in a box."""
    if app is None:
        return
    if isinstance(result, filediff.Identical):
        prompt = tr("The files are identical.")
    elif isinstance(result, filediff.DiffersAt):
        prompt = tr("The files differ at byte {offset}, on line {line}.").format(
            offset=result.offset, line=result.line)
    else:  # a TextDiff whose lines are all the same
        prompt = tr("The files differ only in their line endings.")
    await Dialog(title=tr("Compare files"), prompt=prompt, buttons="ok").execute(app)


async def open_diff(desktop: Any, left: Any, right: Any) -> DiffWindow | None:
    """The files at *left* and *right* compared, and shown side by side on
    *desktop* -- or said in a box when there is nothing to show.  The window,
    or None."""
    app = desktop.application
    result = await compare_files(app, left, right)
    if result is None:
        return None
    if not isinstance(result, filediff.TextDiff) or not result.hunks:
        await say_result(app, result)
        return None
    window = DiffWindow(left, right, model=result)
    desktop.open(window)
    # Once on the desktop, which gives the view its height: the first
    # difference in sight, as ``mcdiff`` opens.
    window.view.go_to(0)
    return window
