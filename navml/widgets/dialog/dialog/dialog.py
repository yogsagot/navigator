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
from navkit.commands import Command
from navkit.events import ClickOutsideEvent, Event
from navkit.reactive import reactive
from navkit.widget import Widget

from navml.widgets.dialog.commands import Cancel, Default, SelectNext, SelectPrevious
from navml.widgets.dialog.history import History
from navml.widgets.dialog.modal import Modal


class Dialog(Modal):
    """A modal window with an OK and a Cancel, and an answer."""

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

    def valid(self) -> bool:
        """Whether OK may close the dialog: Turbo Vision's ``Valid(cmOK)``.

        True unless a derived dialog finds something it cannot accept -- a
        date that is not one, say -- in which case it says so itself and the
        dialog stays up with what the user typed still in it.
        """
        return True

    # -- dismissing -----------------------------------------------------------

    def must_ask(self) -> bool:
        """Whether dismissing needs the dialog's say first: ``Valid(cmCancel)``.

        :meth:`navml.widgets.window.Window.must_ask` for a dialog: False
        unless what the user typed would be lost.  Asked synchronously, so a
        dialog with nothing to lose still comes down in one call.
        """
        return False

    async def ask_to_close(self) -> bool:
        """Say whether the dialog may be dismissed; asked only when :meth:`must_ask`.

        A dialog may be shown from here: :meth:`request_close` starts this as
        a task rather than awaiting it inside a handler.
        """
        return True

    def request_close(self) -> None:
        """Dismiss as the user asked to -- Esc, the close icon, a click outside.

        At once, or after :meth:`ask_to_close`.  :meth:`close` stays the
        unconditional one.  Neither OK nor the Cancel button comes here: a
        press on Cancel is the answer itself, and asking whether it was meant
        would be asking twice.
        """
        if not self.must_ask():
            self.close(None)
            return
        self.spawn(self._close_asking())

    async def _close_asking(self) -> None:
        if await self.ask_to_close() and self.parent is not None:
            self.close(None)

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

    async def activate_shortcut(self, letter: str) -> bool:
        """Alt+*letter* to the first control answering to it, this dialog's own
        buttons last.

        The tree puts them first, for :meth:`focusable`'s reason.  Turbo
        Vision gave the key to the control inserted first, and a resource
        inserted its buttons last, so a caption sharing a letter with
        *Cancel* -- *Compare ~c~ontents*, *~C~ase sensitive* -- won it.
        """
        mine = self.buttons_row
        ordered = [c for c in self.controls() if c not in mine]
        ordered += [c for c in self.controls() if c in mine]
        for control in ordered:
            if control.shortcut_match(letter):
                return await control.activate(letter)
        return False

    @property
    def buttons_row(self) -> tuple[Widget, ...]:
        """This dialog's own buttons, left to right.

        Named rather than listed inline so that a derived dialog adding a
        fourth button can say so in one place.
        """
        return (self.ok, self.no, self.cancel, self.info)

    @property
    def default_button(self) -> Widget | None:
        """The button Enter presses, wherever the focus is."""
        for control in self.controls():
            if getattr(control, "default", False) and control.visible:
                return control
        return None

    # -- commands ------------------------------------------------------------
    #
    # The keys are the markup's ``keys:`` block.  Alt+letter is not among them
    # and is still ``Modal.on_key``'s: which letters mean anything depends on
    # the captions of whatever controls the dialog holds, and a table is fixed
    # when the class is made.

    def enables(self, command: Command) -> bool:
        """Enter needs a default button to press."""
        if isinstance(command, Default):
            return self.default_button is not None
        return super().enables(command)

    async def on_cancel(self, event: Cancel) -> bool:
        self.request_close()
        return True

    async def on_click_outside(self, event: ClickOutsideEvent) -> bool:
        """A click past the dialog is its Esc, where the dialog says so.

        Asked as the Cancel command from where the keyboard is, exactly as the
        key asks it, so a dialog that answers Cancel its own way -- or refuses
        it -- does the same for the click.
        """
        app = self.application
        if app is None or not self.close_on_outside_click:
            return False
        await app.run_command(Cancel)
        return True

    async def on_default(self, event: Default) -> bool:
        return await self.default_button.press()

    async def on_select_next(self, event: SelectNext) -> bool:
        self._application_or_raise().focus_next()
        return True

    async def on_select_previous(self, event: SelectPrevious) -> bool:
        self._application_or_raise().focus_next(reverse=True)
        return True

    def _application_or_raise(self) -> Application:
        app = self.application
        if app is None:  # pragma: no cover - a dialog off the tree
            raise RuntimeError("this dialog is not in an application")
        return app

    # -- what the buttons mean -----------------------------------------------

    async def on_ok_click(self, event: Event) -> bool:
        """``ok`` was clicked, and the generated half said so by name."""
        if not self.valid():
            return True
        self.record_history()
        self.close(self.accept())
        return True

    async def on_no_click(self, event: Event) -> bool:
        """*No* of ``yes-no-cancel`` and ``yes-no``: an answer, and a different one from Cancel's."""
        self.close(False)
        return True

    def record_history(self) -> None:
        """Remember every line in this dialog that has a history button.

        What accepting a dialog did in Turbo Vision, by its ``cmRecordHistory``
        broadcast.  Cancelling records nothing, so a mistyped name abandoned
        with Esc does not come back to be picked.
        """
        stack = list(self.children)
        while stack:
            widget = stack.pop()
            if isinstance(widget, History):
                widget.record()
            stack.extend(widget.children)

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

        It closes without :meth:`must_ask`: pressing Cancel already says the
        changes are to go, where Esc and the close icon may be a slip.
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
