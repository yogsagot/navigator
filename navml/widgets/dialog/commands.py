"""The dialog group's commands: what ``Dialog``, ``TabView`` and ``TreeView`` handle.

Turbo Vision's ``cmCancel`` and ``cmDefault``, and Tab and Shift+Tab, which
are commands here where Turbo Vision had ``TGroup`` select the next view
directly: as commands they are rebindable, and a dialog that wants Tab for
itself can take the key without overriding a method.  And the quick search
every list of names shares -- a file panel's and a tree's alike.  And the
clipboard's four, which an input line and the editor both answer.
"""

from __future__ import annotations

from dataclasses import dataclass

from navkit.commands import Command


class Cancel(Command):
    """Dismiss a dialog without an answer."""

    title = "Cancel"


class Default(Command):
    """Press a dialog's default button, wherever the focus is."""

    title = "OK"


class SelectNext(Command):
    """Move the keyboard to the next control."""


class SelectPrevious(Command):
    """Move the keyboard to the previous control."""


class NextTab(Command):
    """Show the next page of a tabbed dialog."""

    title = "Next tab"


class PreviousTab(Command):
    """Show the previous page of a tabbed dialog."""

    title = "Previous tab"


class QuickSearch(Command):
    """Ctrl+S: type the start of a name and the cursor jumps to it.

    Midnight Commander's key and its rules -- a file panel's and a tree's
    alike, which is why it is the library's.  DOS Navigator 1.51's panel quick
    search -- the *Quick search* choice in ``dlgPanelSetup``, started by an
    Alt+letter -- has no handler in the published source to follow; its tree's
    does (``TREE.PAS``), and the tree follows it.
    """

    title = "Search"



# -- the clipboard ----------------------------------------------------------------
#
# Turbo Vision's ``cmCut``, ``cmCopy``, ``cmPaste`` and ``cmClear``, which an
# input line and the editor both answer -- through their own keys, and through
# their context menus.


class ClipboardCut(Command):
    """``cmCut``: the selection to the clipboard, and out of the text.

    Not ``Cut``/``Copy``/``Paste``: ``Copy`` is F5's, and a handler named
    ``on_copy`` or ``on_paste`` would answer that command or a paste event.
    """

    title = "Cut"


class ClipboardCopy(Command):
    """``cmCopy``: the selection to the clipboard."""

    title = "Copy"


class ClipboardPaste(Command):
    """``cmPaste``: the clipboard at the cursor."""

    title = "Paste"


class Clear(Command):
    """``cmClear``: the selection out of the text, the clipboard untouched."""

    title = "Clear"


class SelectAll(Command):
    """Select the whole text.

    Not Turbo Vision's or DOS Navigator's, neither of which had one; it is
    there for the context menu, which offers it beside Cut, Copy and Paste.
    """

    title = "Select all"

# -- the calendar ----------------------------------------------------------------
#
# What ``CalendarView`` -- a date field's drop-down and the *Calendar* window --
# does besides moving its cursor: keys TVDEMO's ``TCalendarView`` matched in
# ``HandleEvent``, made commands so a menu can show them and Key bindings can
# rebind them.


class PreviousMonth(Command):
    """PgUp: the month before."""

    title = "Previous month"


class NextMonth(Command):
    """PgDn: the month after."""

    title = "Next month"


class PreviousYear(Command):
    """Ctrl+PgUp: the same month a year before."""

    title = "Previous year"


class NextYear(Command):
    """Ctrl+PgDn: the same month a year after."""

    title = "Next year"


class ChooseMonth(Command):
    """M: the list of months dropped under the month's name."""

    title = "Choose month"


class ChooseYear(Command):
    """Y: the list of years dropped under the year."""

    title = "Choose year"


class GoToToday(Command):
    """T: today under the cursor, and the keys back on the days."""

    title = "Go to current date"


@dataclass(frozen=True, slots=True)
class SetCalendarSystem(Command):
    """The calendar the month is shown in, by its key in
    ``navml.calendars.SYSTEMS``.  Not TVDEMO's, whose calendar was Gregorian
    only; answered by whatever holds the view (Navigator's *Calendar* window)."""

    title = "Calendar system"

    calendar: str = "gregorian"


@dataclass(frozen=True, slots=True)
class SetCalendarView(Command):
    """What the *Calendar* window shows of its calendar system, beside the
    Gregorian: ``only`` its month, ``gregorian_grid`` the Gregorian month with
    the day spelled in it, ``selected_grid`` its month with the Gregorian day
    spelled, ``both`` the two months side by side.  Not TVDEMO's either."""

    title = "Calendar view"

    view: str = "selected_grid"


@dataclass(frozen=True, slots=True)
class SwapCalendars(Command):
    """The month in the Gregorian instead of the calendar system, or back --
    the *Calendar* window's ``C``.  Not TVDEMO's either."""

    title = "Swap calendars"


__all__ = [
    "Cancel",
    "ChooseMonth",
    "ChooseYear",
    "Clear",
    "ClipboardCopy",
    "ClipboardCut",
    "ClipboardPaste",
    "Default",
    "GoToToday",
    "NextMonth",
    "NextTab",
    "NextYear",
    "PreviousMonth",
    "PreviousTab",
    "PreviousYear",
    "QuickSearch",
    "SelectAll",
    "SelectNext",
    "SelectPrevious",
    "SetCalendarSystem",
    "SetCalendarView",
    "SwapCalendars",
]

