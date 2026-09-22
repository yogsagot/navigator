"""The descriptor an ``alias`` line compiles to.

Run-time support, a peer of :mod:`navml.component`: generated code imports it,
and nothing else does.  ``alias title: header.text`` becomes one line of the
generated class body::

    class Panel(_Component):
        title: str = _Alias("header", "text")

and reading or writing ``panel.title`` reaches ``panel.header.text``.

**Correctness falls out of the target's own descriptor rather than being
reimplemented here.**  A read is a plain :func:`getattr`, so navkit captures the
dependency at the target's cell -- outside the memoisation, so even a cached
value subscribes.  A write is a plain :func:`setattr`, so it is checked against
the *target's* declared type, refused while the target holds a live binding, and
propagates exactly as a direct write would.  What this module adds is three
things that cannot fall out:

* :meth:`_Alias.cell` answers with the target's cell, which is the one method
  :class:`navkit.reactive.Declaration` documents as an extension point.  Every
  path through that base funnels here, so ``unbind()``, ``is_bound()`` and
  ``peek()`` work through an alias without being told about one -- and so does a
  *chain* of them, because the lookup goes through ``declarations()`` and an
  alias on the target is in that mapping just like a reactive attribute.
* :meth:`_Alias.__set__` re-owns a binding.  ``bind()``'s one argument is the
  object that owns the attribute, and after forwarding that is the *target*, so
  an expression written against the aliasing widget would be handed the wrong
  one.  A ``Label`` has a ``width`` too, so nothing raises and the wrong number
  is computed for ever -- which is why navkit hands out
  :meth:`~navkit.reactive.Binding.owned_by` rather than leaving each caller to
  improvise it.  Doing it in the descriptor means it holds for hand-written
  Python as well as for markup, and that it composes: the wrapper ignores its
  own argument, so through a chain the outermost owner wins.
* Every failure is re-raised naming both ends.  navkit's own message says
  ``Label.text``, which is true and unhelpful: the author wrote ``Panel.title``
  and usually cannot edit ``Label`` at all.

*Aliases* in ``navml/DESIGN.md`` records why each of these went the way it did,
including the three things an alias deliberately cannot carry -- an initial
value, an ``equal=`` and a cell of its own.
"""

from __future__ import annotations

from typing import Any

from navkit.reactive import (
    Binding,
    Declaration,
    ReactiveError,
    declarations,
)


class _Alias(Declaration):
    """An attribute that forwards to one on another widget in the document.

    *target* is an ``id`` the document declares and *attribute* the name of a
    reactive attribute on whatever that id names.  Exactly one property deep,
    always: reach goes further by chaining aliases, so that every hop is an
    export the component in the middle declared.
    """

    def __init__(self, target: str, attribute: str):
        self.target = target
        self.attribute = attribute
        #: An alias has no cell of its own, so there is nowhere to put a
        #: comparator: the one that counts belongs to the target's declaration.
        self.equal = None
        self.name = "<alias>"

    # -- the forwarding itself ----------------------------------------------

    def cell(self, obj: object) -> Any:
        """The *target's* cell, which is the whole of the override.

        Resolved through :func:`~navkit.reactive.declarations` rather than
        ``getattr(type(widget), self.attribute)`` so that an alias whose target
        is itself an alias forwards again instead of stopping at a descriptor
        that owns nothing.
        """
        widget = self._widget(obj)
        return self._declaration(obj, widget).cell(widget)

    def __get__(self, obj: object | None, objtype: type | None = None) -> Any:
        # Answering with the declaration for a class-level read is not
        # cosmetic: `unbind(panel, Panel.title)' and its two siblings check
        # `getattr(type(obj), name) is attribute', and would refuse an alias
        # that handed back anything else.
        if obj is None:
            return self
        widget = self._widget(obj)
        try:
            return getattr(widget, self.attribute)
        except ReactiveError as error:
            raise self._restated(obj, error) from error

    def __set__(self, obj: object, value: Any) -> None:
        widget = self._widget(obj)
        if isinstance(value, Binding):
            value = value.owned_by(obj)
        try:
            setattr(widget, self.attribute, value)
        except (ReactiveError, AttributeError) as error:
            raise self._restated(obj, error) from error

    # -- saying which alias it was ------------------------------------------

    def _widget(self, obj: object) -> Any:
        """Whatever the target id names, or a failure that says so.

        The interesting way for this to fail is an alias read before the
        generated ``__init__`` has run -- from a base component's constructor,
        say -- where the bare ``AttributeError`` names only the id.
        """
        try:
            return getattr(obj, self.target)
        except AttributeError as error:
            raise ReactiveError(
                f"{self._where(obj)}: {type(obj).__name__} has no {self.target}"
                f" yet; an alias reaches its target only once the generated"
                f" __init__ has built the tree"
            ) from error

    def _declaration(self, obj: object, widget: object) -> Declaration:
        declaration = declarations(type(widget)).get(self.attribute)
        if declaration is None:
            raise ReactiveError(
                f"{self._where(obj)}: {self.attribute} is not a reactive "
                f"attribute of {type(widget).__name__}"
            )
        return declaration

    def _restated(self, obj: object, error: Exception) -> Exception:
        """*error* from the target end, said again naming both ends."""
        return type(error)(f"{self._where(obj)}: {error}")

    def _where(self, obj: object | None = None) -> str:
        owner = type(obj).__name__ if obj is not None else self._owner()
        return f"{owner}.{self.name} -> {self.target}.{self.attribute}"

    def _owner(self) -> str:
        return getattr(self.declaring_class, "__name__", "?")

    def __repr__(self) -> str:
        return f"<alias {self._where()}>"
