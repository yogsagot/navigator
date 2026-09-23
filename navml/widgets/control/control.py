"""What every widget a dialog can put the keyboard into has in common.

Written in Python alone, and deliberately: a `Control` places nothing and
paints nothing, so a markup half would splice a generated class for an empty
tree into the MRO of every widget in the library.  It is the second live
example of the Python-only shape beside `Spacer`, and the first one that earns
it by being a base rather than a leaf.

Three things live here, and each is the same in every control that has it:

* **`disabled`**, which is a *state* and so reactive, and which takes the
  control out of the tab order without anything else being told.
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
from navkit.reactive import bind, computed, reactive
from navkit.widget import Widget


def parse_shortcut(text: str) -> tuple[str, int, str]:
    """Split ``"~O~K"`` into the caption, where the marked letter is, and it.

    Returns ``("OK", 0, "o")``: the text with its tildes removed, the index in
    *that* string at which the marked run begins, and the letter folded to
    lower case -- because `KeyEvent.key` is lower case and the comparison has
    to happen somewhere.

    Turbo Vision's own spelling, and worth keeping rather than inventing a
    property: the mark travels with the caption, so a translated caption
    carries its own accelerator and nothing has to be kept in step with it.
    ``~~`` is a literal tilde, and an unpaired ``~`` is drawn as one -- a
    caption is text first and a declaration second.
    """
    out: list[str] = []
    start, letter = -1, ""
    index = 0
    while index < len(text):
        char = text[index]
        if char != "~":
            out.append(char)
            index += 1
            continue
        if text[index + 1 : index + 2] == "~":
            out.append("~")          # `~~' is one literal tilde
            index += 2
            continue
        closing = text.find("~", index + 1)
        if closing == -1:
            out.append("~")          # unpaired: drawn, not obeyed
            index += 1
            continue
        if start == -1:
            start = len(out)
            marked = text[index + 1 : closing]
            letter = marked[:1].lower()
        out.append(text[index + 1 : closing])
        index = closing + 1
    caption = "".join(out)
    return caption, start, letter


class Control(Widget):
    """A widget a dialog can put the keyboard into."""

    #: Refused input, painted greyed, and out of the tab order.  Spelled
    #: positively rather than as `enabled' because that is the only spelling a
    #: sheet can use: `:state' matches a truthy attribute and the selector
    #: grammar has no `:not()', so `Button:disabled { }' is one line while
    #: `enabled' could never reach the case DOS Navigator gives a colour slot
    #: of its own.
    disabled: bool = reactive(False)

    #: Whether this control would take the keyboard if it were enabled.  A
    #: class fact rather than an instance one, so plain: a `Label' is never
    #: focusable and a `Button' always is, and neither changes its mind.
    accepts_focus: bool = True

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Bound rather than assigned, so that `disabled' is the only thing
        # anybody sets and the tab order follows it.  That makes `can_focus'
        # read-only on a control -- the same shape as *A property a widget
        # navigates cannot be bound*, arrived at from the other end.
        self.can_focus = bind(lambda o: o.accepts_focus and not o.disabled)

    @property
    def caption(self) -> str:
        """The text this control's ``~A~`` is marked in.

        A plain property so that a control whose caption is not called ``text``
        -- a cluster's item, say -- can answer differently without declaring a
        second attribute.
        """
        return getattr(self, "text", "")

    @computed
    def shortcut(self) -> str:
        """The letter that reaches this control, lower case, or ``""``."""
        return parse_shortcut(self.caption)[2]

    def shortcut_match(self, letter: str) -> bool:
        """Whether *letter* reaches this control right now."""
        return (
            bool(self.shortcut)
            and self.shortcut == letter.lower()
            and self.visible
            and not self.disabled
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
        if event.action == "press" and event.button == "left" and not self.disabled:
            self.focus()
        return False
