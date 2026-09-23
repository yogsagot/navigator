# navml: generated
"""Generated from ``window.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component

__navml_component__ = "Window"

__all__ = ["Window"]


class Window(_Component):
    """A detached window on a desktop: dragged, resized, zoomed and raised.

    Turbo Vision's ``TWindow``, and what DOS Navigator's file panels, viewer
    and editor all are.  It lives in a :class:`~navml.widgets.desktop.Desktop`,
    which owns the z-order and says which window is active; the window owns
    its own rectangle and the chrome that changes it.

    **Nothing about the geometry is written here, and that is the rule this
    component exists under.**  A drag assigns ``x`` and ``y``, a resize assigns
    ``width`` and ``height``, a zoom assigns all four -- and a bound attribute
    is read-only until something unbinds it.  So the rectangle is *state*, like
    a panel's ``path``: a derived document may give it a starting value with a
    literal line, which is an assignment and not a binding, and may never bind
    it.  See *A property a widget navigates cannot be bound* in DESIGN.md.
    """

    #: The document this class was generated from.
    __navml_source__ = "window.nml"

    #: Shown centred on the top edge of a framed window.
    title: str = _reactive('')    # window.nml:17

    #: Whether the ``[■]`` icon is painted, and answers a click.
    closable: bool = _reactive(True)    # window.nml:20

    #: Whether the ``[↑]`` icon is painted, and the title answers a double
    #: click.
    zoomable: bool = _reactive(True)    # window.nml:24

    #: Whether the bottom-right corner is a grip.
    resizable: bool = _reactive(True)    # window.nml:27

    #: The smallest a resize may make it.  Turbo Vision's ``minWinSize``.
    min_width: int = _reactive(16)    # window.nml:30
    min_height: int = _reactive(6)    # window.nml:31

    #: Filling the whole desktop, with the rectangle it came from kept aside.
    #: Declared here so that a derived document can open zoomed with one
    #: literal line; toggled by :meth:`toggle_zoom`, never bound.
    zoomed: bool = _reactive(False)    # window.nml:36

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
