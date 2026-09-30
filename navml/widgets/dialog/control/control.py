"""What every widget a dialog can put the keyboard into has in common.

Written in Python alone, and deliberately: a `Control` places nothing and
paints nothing, so a markup half would splice a generated class for an empty
tree into the MRO of every widget in the library.  It is the second live
example of the Python-only shape beside `Spacer`, and the first one that earns
it by being a base rather than a leaf.

Three things live here, and each is the same in every control that has it:

* **the tab order following `inert`**, so that setting `Widget.disabled` on
  the control or on anything holding it takes the control out of the order
  without anything else being told.
* **the `~A~` shortcut**, parsed once so that ten widgets do not each parse it,
  and reachable as the letter a container looks for.
* **focus on a mouse press**, which is what a pointing device means by
  "this one", and which no widget should have to remember.

Read `A component is a directory` in `navml/DESIGN.md` for why this is a
directory holding one file.
"""

from __future__ import annotations

from typing import Any

from navkit.events import MouseClickEvent
from navkit.reactive import bind, computed
from navkit.widget import Widget

from navml.component import take_declared


def caption_runs(text: str) -> list[tuple[str, bool]]:
    """*text* as runs of plain and marked characters, in order.

    What Turbo Vision's ``MoveCStr`` drew: every ``~`` toggles the highlight,
    so a caption may mark more than one run -- DOS Navigator's Copy prompt
    marks the file name as well as its letter.  ``~~`` is one literal tilde,
    inside a marked run as well as outside one, which is what lets a file
    name be put in a caption; a ``~`` left over with nothing to pair with is
    drawn as one too -- a caption is text first and a declaration second.
    """
    toggles: list[int] = []
    index = 0
    while index < len(text):
        if text[index] == "~":
            if text[index + 1 : index + 2] == "~":
                index += 2
                continue
            toggles.append(index)
        index += 1
    if len(toggles) % 2:
        toggles.pop()                # unpaired: drawn, not obeyed
    toggle_at = set(toggles)
    runs: list[tuple[str, bool]] = []
    current: list[str] = []
    marked = False
    index = 0
    while index < len(text):
        if index in toggle_at:
            if current:
                runs.append(("".join(current), marked))
                current = []
            marked = not marked
            index += 1
            continue
        if text[index : index + 2] == "~~":
            current.append("~")      # `~~' is one literal tilde
            index += 2
            continue
        current.append(text[index])
        index += 1
    if current:
        runs.append(("".join(current), marked))
    return runs


def parse_shortcut(text: str) -> tuple[str, int, str]:
    """Split ``"~O~K"`` into the caption, where the marked letter is, and it.

    Returns ``("OK", 0, "o")``: the text with its tildes removed, the index in
    *that* string at which the marked run begins, and the letter folded to
    lower case -- because `KeyEvent.key` is lower case and the comparison has
    to happen somewhere.

    Turbo Vision's own spelling, and worth keeping rather than inventing a
    property: the mark travels with the caption, so a translated caption
    carries its own accelerator and nothing has to be kept in step with it.
    Only the first marked run is the shortcut; :func:`caption_runs` has the
    rules for the rest, ``~~`` and an unpaired ``~`` among them.
    """
    out: list[str] = []
    start, letter = -1, ""
    for run, marked in caption_runs(text):
        if marked and start == -1:
            start = len("".join(out))
            letter = run[:1].lower()
        out.append(run)
    return "".join(out), start, letter


def escape_caption(text: str) -> str:
    """*text* with every ``~`` doubled, so a file name is drawn as it is."""
    return text.replace("~", "~~")


class Control(Widget):
    """A widget a dialog can put the keyboard into."""

    #: Whether this control would take the keyboard if it were enabled.  A
    #: class fact rather than an instance one, so plain: a `Label' is never
    #: focusable and a `Button' always is, and neither changes its mind.
    accepts_focus: bool = True

    def __init__(self, **kwargs: Any) -> None:
        # The same keywords a markup-built component takes, so that a control
        # written in Python alone -- `CheckBoxes', `RadioButtons' -- has the
        # constructor its neighbours have.  `Component.__init__' does this for
        # anything with a document; nothing did it for anything without one,
        # and the difference reached the call site.
        take_declared(self, kwargs)
        super().__init__(**kwargs)
        # Bound rather than assigned, so that `disabled' is the only thing
        # anybody sets and the tab order follows it -- through `inert', so a
        # disabled container takes its controls out of the order as well.  That makes `can_focus'
        # read-only on a control -- the same shape as *A property a widget
        # navigates cannot be bound*, arrived at from the other end.
        self.can_focus = bind(lambda o: o.accepts_focus and not o.inert)

    @computed
    def shortcut(self) -> str:
        """The letter that reaches this control, lower case, or ``""``.

        Read off ``text`` with a :func:`getattr`, not through a property of
        its own.  A property would be a second name for the caption, and the
        generator refuses an ``id`` that collides with a class attribute --
        which is how this was found: ``Button``'s caption child is called
        ``caption``, and so was the property.  A control whose caption is not
        ``text`` at all, like a cluster's items, parses its own.
        """
        return parse_shortcut(getattr(self, "text", ""))[2]

    def shortcut_match(self, letter: str) -> bool:
        """Whether *letter* reaches this control right now."""
        return (
            bool(self.shortcut)
            and self.shortcut == letter.lower()
            and self.visible
            and not self.inert
        )

    async def activate(self, letter: str = "") -> bool:
        """What the shortcut does.  Focusing, unless a subclass says more."""
        return self.focus()

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """Take the keyboard on a press, and claim nothing.

        Returning False is the point: focusing is not answering.  A `Button'
        calls up to this and *then* decides whether the press also means a
        click, which is what lets a control be focusable without becoming a
        target for every press that lands on it.
        """
        if event.action == "press" and event.button == "left" and not self.inert:
            self.focus()
        return False
