"""The base every generated class shares.

`navml/DESIGN.md`'s *Whether the generated half gets a base of its own* asked
for this and listed what it would hold.  It holds three things, and each one
was otherwise going to be repeated in every file the code generator writes:

* :meth:`Component.layout`, which sizes the widget and **does not cascade into
  its children**, because a component whose children are all placed by markup
  does not want the inherited cascade.  It was byte-identical in all four
  hand-written stand-ins, which is what the argument for a base rested on.
* :meth:`Component.__init__`, which is how a value gets into a component from
  outside.  :class:`~navkit.widget.Widget`'s own constructor is keyword-only
  and *closed*, so without this a component could not be handed anything it
  declares.
* ``__navml_source__``, the markup a class was generated from -- somewhere for
  provenance to live, which it had not had.

**What this is not is a test of componenthood.**  It is true of a component
written in markup and false of one written in Python -- `navml/widgets/spacer/spacer.py`
is a component and is not a :class:`Component` -- so it answers *built from
markup* and may never be read as *is a component*.  That asymmetry has one
visible consequence, and it is visible to people who never read Python:
:func:`navkit.stylesheet._is_a` matches a type selector by class **name**
walking the MRO, so ``Component { }`` is a live ``.nss`` selector matching every
markup-built widget and no hand-written one.  Underscoring the name the
generator imports it under does not hide ``__name__``; nothing can.
"""

from __future__ import annotations

import inspect
from typing import Any

from navkit.reactive import declarations, is_bound
from navkit.widget import Widget

#: What :meth:`navkit.widget.Widget.__init__` accepts, read off the signature
#: rather than spelled out, so the two cannot drift apart.  Everything else a
#: caller passes is either something the component declares or a mistake, and
#: :meth:`Component.__init__` keeps that distinction by handing the mistakes on
#: to the constructor that already refuses them.
_WIDGET_PARAMETERS = frozenset(inspect.signature(Widget.__init__).parameters) - {
    "self"
}


class Component(Widget):
    """A widget whose tree was declared in markup."""

    #: The document this class was generated from, as a file name.  Empty on
    #: anything that was not generated, and filled by the code generator.
    __navml_source__: str = ""

    def __init__(self, **kwargs: Any) -> None:
        """Take the component's own declarations out of *kwargs* and set them.

        A component's parameters are the properties it declares -- markup has
        no parameter list and grows none -- and this is what makes that true:
        ``Manager(left_path=a)`` reaches ``Manager.left_path`` while
        ``Manager(width=10)`` goes on reaching ``Widget.__init__`` as it
        always did.  A keyword naming neither is left in *kwargs* and raises
        there, so a typo still fails at the call, loudly, with the name in it.

        **Set before the tree is joined, not after.**  ``Widget.__init__``
        finishes by calling ``parent.add(self)``, which lays the widget out and
        runs its ``mounted()`` -- so a value assigned afterwards would arrive
        after the callbacks that most want to read it.  The cells these writes
        create do not need ``Widget.__init__`` to have run: a cell belongs to
        the instance and is made on first touch.
        """
        declared = declarations(type(self))
        mine = {
            name: kwargs.pop(name)
            for name in list(kwargs)
            if name not in _WIDGET_PARAMETERS and name in declared
        }
        for name, value in mine.items():
            setattr(self, name, value)
        super().__init__(**kwargs)

    def layout(self, width: int, height: int) -> None:
        """Size only this widget: its children are placed by the markup.

        :meth:`navkit.widget.Widget.layout` cascades the parent's size into
        every child whose own size is not bound, which is what a hand-written
        widget wants and what a generated one must not have: markup has already
        said where each child goes.  Stopping here is also what lets a literal
        ``height: 1`` compile to a plain assignment rather than to a binding
        that exists only to protect the constant from this cascade.

        A markup child that says nothing about its size therefore stays zero
        rather than silently filling its parent, which is the honest failure --
        the size is missing from the document and the screen says so.
        """
        if not is_bound(self, Widget.width):
            self.width = width
        if not is_bound(self, Widget.height):
            self.height = height
