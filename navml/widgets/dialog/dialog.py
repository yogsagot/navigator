"""The handlers behind ``dialog.nml``.

The worked example of the other direction from :mod:`navml.widgets.button`:
Button declares an event and *emits* it, and Dialog is what has three of them
inside it and has to tell which one spoke.  It never asks.  The generated half
wires each id'd child to an ``on_<id>_<event>`` method, so the question is
answered by the time this file runs -- see *Which child it was is a question
the generator answers* in ``navml/DESIGN.md``.

All three mechanisms are in here at once, which is the point of the example:

* ``ok`` overrides its generated stub, and claims the click.
* ``cancel`` does not, so its stub declines and the click carries on up to
  this class's own ``on_click`` -- the general handler, still reached, still
  free to catch every button the file did not name.  A stub nobody overrides
  costs exactly nothing, which is what makes it safe for the generator to
  write one for every child without being told.
* ``info`` is routed by an explicit markup line, because :meth:`show_info` is
  named for what the dialog *does* rather than for what happened to it.  That
  method is deliberately not an ``on_*``: the prefix means navkit found it
  under ``event.handler``, and this one was found by one line of markup.
"""

from __future__ import annotations

from navkit.events import Event
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget


class Dialog(Widget):
    """A prompt with an OK, a Cancel and a Help button."""

    #: True once OK was clicked, False once the dialog was dismissed, None
    #: while it is still up.  A *state*, so reactive -- the division the whole
    #: event mechanism rests on.
    result: bool | None = reactive(None)

    async def on_ok_click(self, event: Event) -> bool:
        """``ok`` was clicked.

        Which button that was is not a question this method asks: the name it
        is called by is the answer, composed by the generator from the ``id:``
        line and the handler navkit derives from the event class.
        """
        self.result = True
        return True

    async def on_click(self, event: Event) -> bool:
        """Any click inside the dialog that nothing more specific claimed.

        Which is ``cancel``, whose generated stub declined, and would be any
        button a later revision of the markup adds without a handler.  The
        specific hook does not take the general one away; it sits in front of
        it, the same order :meth:`navkit.widget.Widget.emit` already walks in.
        """
        self.result = False
        return True

    async def show_info(self, event: Event) -> None:
        """Reached from ``dialog.nml``'s one ``on_click:`` line.

        A markup handler is one line and always consumes, so everything the
        line cannot say lives here.  It returns nothing: the generated
        function supplies the ``return True`` on its own.
        """
        self.prompt = "OK accepts, Cancel dismisses."

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
        if self.width >= 2 and self.height >= 2:
            surface.draw_box(
                0, 0, self.width, self.height, *self.box_charset(), self.style
            )
