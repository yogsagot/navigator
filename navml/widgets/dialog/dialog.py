"""The handlers behind ``dialog.nml``.

Two things worth reading this file for.

**Which child spoke is never asked.**  The generated half wires each id'd
child to an ``on_<id>_<event>`` method, so the question is answered by the
time this file runs -- see *Which child it was is a question the generator
answers* in ``navml/DESIGN.md``.  ``ok`` and ``cancel`` each override their
stub; a button a later revision adds without one falls through to this
class's own ``on_click``, which is still reached and still free to catch it.

**A handler starts a dialog; it does not wait for one.**  :meth:`execute` is a
coroutine that returns when the dialog closes, and it must be started with
``Application.spawn`` rather than awaited from inside a handler.
``_main_loop`` awaits ``_handle`` and only then paints, so a handler that
waits is holding the event queue's only consumer: the dialog is never drawn,
the key that would dismiss it is never dispatched, and the terminal is frozen
with the old frame on it.  Measured, not reasoned -- and :meth:`execute`
refuses outright rather than hanging, because a diagnosable error at the call
site is worth three lines.
"""

from __future__ import annotations

import asyncio
from typing import Any

from navkit.application import Application
from navkit.events import Event, KeyEvent
from navkit.reactive import reactive
from navkit.widget import Widget

from navml.widgets.window import Window


class Dialog(Window):
    """A modal window with an OK and a Cancel, and an answer."""

    #: All input while it is mounted.  Read by the mount walk, which pushes
    #: the dialog onto the application's modal stack before ``mounted()``
    #: runs -- so Tab containment, the focus claim and the focus restore are
    #: all navkit's and none of them is repeated here.
    modal: bool = True

    #: What OK meant, readable while the dialog is still up.  A *state*, so
    #: reactive; :meth:`execute`'s return value is this at the moment it
    #: closed, and ``None`` means cancelled.
    result: Any = reactive(None)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._pending: asyncio.Future[Any] | None = None

    # -- running it ----------------------------------------------------------

    async def execute(self, app: Application | None = None) -> Any:
        """Show the dialog and answer when it closes.

        Start it with :meth:`navkit.widget.Widget.spawn`, never with a bare
        ``await`` inside a handler -- the module docstring says why, and the
        first line here refuses the mistake instead of hanging.
        """
        app = app if app is not None else self.application
        if app is None:
            raise RuntimeError("a dialog needs an application to be shown in")
        if getattr(app, "_dispatching", False):
            raise RuntimeError(
                "Dialog.execute() cannot be awaited from an event handler: the "
                "handler holds the event loop that would paint the dialog and "
                "deliver its keys, so nothing would happen.  Start it with "
                "self.spawn(...) and let the handler return."
            )
        if self._pending is not None:
            raise RuntimeError(f"{type(self).__name__} is already showing")
        self._pending = asyncio.get_running_loop().create_future()
        app.overlay(self)
        try:
            return await self._pending
        finally:
            self._pending = None
            # Guarded because the application may have stopped while this was
            # waiting, which is what cancels the task that started it.
            if self.parent is not None:
                self.parent.remove(self)

    def close(self, result: Any = None) -> None:
        """Answer with *result* and come down."""
        self.result = result
        if self._pending is not None and not self._pending.done():
            self._pending.set_result(result)
        elif self._pending is None and self.parent is not None:
            # Shown without `execute' -- by `overlay' directly, say.
            self.parent.remove(self)

    def accept(self) -> Any:
        """What OK means.  ``True`` unless a derived dialog says otherwise."""
        return True

    def unmounting(self) -> None:
        """Answer anyway, if something else took the dialog out of the tree.

        A replaced root or an ancestor going with it leaves whoever is
        awaiting :meth:`execute` owed an answer, and ``None`` is the same
        answer a cancel gives.
        """
        if self._pending is not None and not self._pending.done():
            self._pending.set_result(None)
        super().unmounting()

    # -- focus ---------------------------------------------------------------

    def focusable(self) -> list[Widget]:
        """The tab order, with this dialog's own buttons last.

        A generated ``__init__`` calls ``super().__init__()`` first, so a
        *derived* dialog's controls are built after this one's buttons and
        land after them in the tree -- which would open every dialog with the
        focus on OK and run Tab backwards.  One override fixes both, because
        ``_claim_focus`` reads the first of this list and ``focus_next`` reads
        the same list.
        """
        order = super().focusable()
        mine = [w for w in self.buttons_row if w in order]
        return [w for w in order if w not in mine] + mine

    @property
    def buttons_row(self) -> tuple[Widget, ...]:
        """This dialog's own buttons, left to right.

        Named rather than listed inline so that a derived dialog adding a
        fourth button can say so in one place.
        """
        return (self.ok, self.cancel, self.info)

    @property
    def default_button(self) -> Widget | None:
        """The button Enter presses, wherever the focus is."""
        for control in self.controls():
            if getattr(control, "default", False) and control.visible:
                return control
        return None

    # -- keys ----------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if event.matches("escape"):
            self.close(None)
            return True
        if event.matches("tab"):
            self._application_or_raise().focus_next()
            return True
        if event.matches("shift+tab"):
            self._application_or_raise().focus_next(reverse=True)
            return True
        if event.matches("enter"):
            button = self.default_button
            if button is not None:
                return await button.press()
            return False
        # Alt+letter, and whatever else Window knows about.
        return await super().on_key(event)

    def _application_or_raise(self) -> Application:
        app = self.application
        if app is None:  # pragma: no cover - a dialog off the tree
            raise RuntimeError("this dialog is not in an application")
        return app

    # -- what the buttons mean -----------------------------------------------

    async def on_ok_click(self, event: Event) -> bool:
        """``ok`` was clicked, and the generated half said so by name."""
        self.close(self.accept())
        return True

    async def on_click(self, event: Event) -> bool:
        """Any click a more specific handler did not claim.

        Which is ``cancel``, whose generated stub declines, and would be any
        button a later revision of the markup adds without a handler.  The
        specific hook does not take the general one away; it sits in front of
        it, the same order ``Widget.emit`` already walks in -- and dismissing
        is the right thing for a button this class has not been told about.

        A stub nobody overrides costs exactly nothing, which is what makes it
        safe for the generator to write one for every child without being
        told to.
        """
        self.close(None)
        return True

    async def show_info(self, event: Event) -> None:
        """Reached from ``dialog.nml``'s one ``on_click:`` line.

        Deliberately not an ``on_*``: that prefix means navkit found the
        method under ``event.handler``, and this one was found by a line of
        markup.  A markup handler is one line and always consumes, so
        everything the line cannot say lives here -- and it returns nothing,
        because the generated function supplies the ``return True``.
        """
        self.prompt = "Enter accepts, Escape dismisses."
