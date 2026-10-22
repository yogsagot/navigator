# navml: generated
"""Generated from ``modal.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component

__navml_component__ = "Modal"

__all__ = ["Modal"]


class Modal(_Component):
    """A fixed, centred box that holds all input until it closes.

    DOS Navigator's ``[33] Frame/background`` and ``[34] Frame icons``, and
    Turbo Vision's ``TDialog`` frame.  It paints the frame, centres the title on
    the top edge, and puts a close icon in the corner -- and it is what carries
    the ``Alt+letter`` walk, because it is the smallest thing that holds a whole
    set of controls.

    **It is not a window**, and the difference is structural rather than a
    flag.  A :class:`~navml.widgets.window.Window` lives on a desktop, moves,
    resizes and changes places with its neighbours; a modal is overlaid on the
    application's root, one level *above* every desktop, so no window can be
    raised past it and nothing outside it is reachable until it is gone.

    **The geometry is bound, and that is not a style choice.**  ``Widget.add``
    lays a child out into its parent's size, and ``Component.layout`` only
    steps around a side that carries a *binding* -- so a modal whose width is a
    literal is resized to the whole terminal the moment it is overlaid.
    Routing the size through a declared property is also what lets a derived
    document change it: ``modal_width: 44`` is a literal onto an attribute
    nothing has bound, where ``width: 44`` would be a value over a live binding
    and would raise.  And because it is bound it is never dragged, which is
    exactly what a modal is.
    """

    #: The document this class was generated from.
    __navml_source__ = "modal.nml"

    #: Shown centred on the top edge, with a space either side of it.
    title: str = _reactive('')    # modal.nml:26

    #: Whether the ``[■]`` icon is painted, and the corner answers a click.
    closable: bool = _reactive(True)    # modal.nml:29

    #: The size the modal asks for.  Overridden by a derived document.
    modal_width: int = _reactive(50)    # modal.nml:32
    modal_height: int = _reactive(10)    # modal.nml:33

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)

        self.width = _bind(lambda _o: _o.modal_width)    # modal.nml:35
        self.height = _bind(lambda _o: _o.modal_height)    # modal.nml:36
        self.x = _bind(lambda _o: max(0, (_o.parent.width - _o.width) // 2))    # modal.nml:37
        self.y = _bind(lambda _o: max(0, (_o.parent.height - _o.height) // 2))    # modal.nml:38
