"""Observable attributes and the bindings between them.

A reactive attribute looks like an ordinary attribute but remembers who read
it.  Assigning one marks every attribute derived from it out of date; the next
read recomputes exactly those that are actually needed.  So a value is never
stale, and never recomputed more often than it is used.

Two declarations cover everything a widget class needs::

    class Panel(Widget):
        cursor = reactive(0)
        entries = reactive(factory=list)

        @computed
        def selected(self) -> DirEntry | None:
            return self.entries[self.cursor] if self.entries else None

and one runtime call covers what markup needs, where the expression belongs to
a single *instance* rather than to the class::

    bind(panel, "width", lambda w: w.parent.width // 2)

Dependencies are discovered by running the expression and noting what it read,
so nothing is ever declared twice and a conditional expression subscribes only
to the branch it actually took.

The propagation is push-pull.  A write eagerly walks the graph marking
dependents stale -- cheap, and it stops at anything already marked -- but
recomputes nothing.  Values are recomputed lazily on read and memoised, which
makes the system glitch-free by construction: a diamond-shaped dependency is
recomputed once, from inputs that are all final, and no observer can catch it
half updated.  That is the same discipline the event loop uses one layer up,
where a whole batch of events is dispatched before a single frame is painted.

Impure reactions -- rescanning a directory when a path changes -- cannot wait
to be read, so they are :func:`effect` nodes: the only eager part of the graph.
They are queued on write and drained by the application between dispatching a
batch of events and painting the frame, never during a paint.

Two rules the rest of the project has to live with:

* An object carrying reactive attributes needs a ``__dict__``, because that is
  where its cells live.  :class:`~navkit.style.Style` and other slotted value
  types therefore cannot host them -- which is right, they are values.
* A collection has to be *replaced* to count as changed.  Mutating a list in
  place and assigning it back over itself changes nothing observable, because
  the equality guard sees the same object.  Build a new list instead.
"""

from __future__ import annotations

import contextlib
import itertools
import weakref
from collections.abc import Callable, Iterator
from enum import IntEnum
from typing import Any, Generic, TypeVar, overload

T = TypeVar("T")

#: Where an object's cells live in its ``__dict__``.
_CELLS = "_reactive_cells"
#: Where an object's effects live, so they last exactly as long as it does.
_EFFECTS = "_reactive_effects"

#: Hands out the declaration order that decides how a flush is sequenced.
_order = itertools.count()


class ReactiveError(RuntimeError):
    """The reactive graph was used in a way that cannot be made to work."""


class CycleError(ReactiveError):
    """A value depends on itself, directly or through other values."""


class _State(IntEnum):
    """How much a cell knows about whether its value is still good.

    ``CHECK`` is the interesting one: a source further upstream changed, but
    something in between may have absorbed the change by recomputing to an
    equal value, so this cell has to ask before it recomputes.
    """

    CLEAN = 0
    CHECK = 1
    DIRTY = 2


def _equal(old: object, new: object) -> bool:
    """True if replacing *old* with *new* changes nothing observable.

    Identity is checked first, which is also why a list mutated in place and
    then assigned back looks unchanged; pass ``equal=`` if a type needs other
    treatment.  A comparison that refuses to produce a bool counts as a
    change, because guessing the other way loses updates silently.
    """
    if old is new:
        return True
    try:
        return bool(old == new)
    except Exception:
        return False


# -- the tracking stack -------------------------------------------------------

#: The cells currently being computed, innermost last.  ``None`` marks an
#: :func:`untracked` region, which hides the frames below it from reads.
_stack: list[_Cell | None] = []


@contextlib.contextmanager
def untracked() -> Iterator[None]:
    """Read reactive attributes without subscribing to them.

    Nests: the marker is pushed and popped like any other frame, so a tracked
    computation resumes tracking once the region ends.  It grants no licence
    to write -- a computed is still pure inside one.
    """
    _stack.append(None)
    try:
        yield
    finally:
        _stack.pop()


def _reader() -> _Cell | None:
    """The cell a read should be attributed to, if any."""
    return _stack[-1] if _stack else None


def _check_writable(cell: _Cell) -> None:
    """Refuse a write made from inside a computed.

    Computeds have to be pure: they are recomputed at unpredictable moments,
    including in the middle of composing a frame, so a computed that assigns
    would turn painting into a source of state changes.  Effects exist for
    exactly that job and are allowed to write.
    """
    for frame in reversed(_stack):
        if frame is not None and not frame.writable:
            raise ReactiveError(
                f"{frame.label} is computed and may not assign {cell.label}"
            )


# -- cells --------------------------------------------------------------------


class _Cell:
    """One observable value belonging to one object.

    A cell with no ``compute`` is a source: it holds whatever was assigned to
    it.  Give it a ``compute`` -- at class level with :func:`computed`, or per
    instance with :func:`bind` -- and it derives its value instead.  The two
    are deliberately the same object, because attaching a binding to a plain
    attribute at runtime is what markup needs to do.
    """

    #: Computeds may not assign reactive attributes; effects may.
    writable = False

    __slots__ = (
        "__weakref__",
        "compute",
        "computing",
        "deps",
        "equal",
        "error",
        "name",
        "owner",
        "state",
        "subscribers",
        "value",
        "version",
    )

    def __init__(
        self,
        owner: object,
        name: str,
        *,
        value: Any = None,
        compute: Callable[[Any], Any] | None = None,
        equal: Callable[[Any, Any], bool] | None = None,
    ):
        self.name = name
        self.owner = weakref.ref(owner)
        self.value = value
        self.error: BaseException | None = None
        self.version = 0
        self.state = _State.DIRTY if compute is not None else _State.CLEAN
        self.compute = compute
        self.equal = equal or _equal
        self.deps: dict[_Cell, int] = {}
        # Weak, so a widget dropped from the tree is not kept alive by
        # whatever it used to derive its geometry from.
        self.subscribers: weakref.WeakSet[_Cell] = weakref.WeakSet()
        self.computing = False

    @property
    def label(self) -> str:
        """How this cell names itself in an error message."""
        owner = self.owner()
        return f"{type(owner).__name__}.{self.name}" if owner else self.name

    def __repr__(self) -> str:
        return f"<cell {self.label}>"

    # -- reading --------------------------------------------------------------

    def get(self) -> Any:
        """Return the current value, subscribing whoever is asking."""
        self._validate()
        reader = _reader()
        if reader is not None and reader is not self:
            reader.deps[self] = self.version
            self.subscribers.add(reader)
        if self.error is not None:
            raise self.error
        return self.value

    def _validate(self) -> None:
        """Bring the value up to date, doing as little work as possible."""
        if self.compute is None or self.state is _State.CLEAN:
            return
        if self.computing:
            raise CycleError(f"{self.label} depends on itself")
        if self.state is _State.CHECK:
            # Something upstream moved, but perhaps not in a way that reaches
            # here: ask every dependency for its version before deciding to
            # run the expression again.
            for dep, seen in list(self.deps.items()):
                dep._validate()
                if dep.version != seen:
                    break
            else:
                self.state = _State.CLEAN
                return
        self._recompute()

    def _recompute(self) -> None:
        owner = self.owner()
        if owner is None or self.compute is None:
            self.state = _State.CLEAN
            return

        previous, self.deps = self.deps, {}
        self.computing = True
        _stack.append(self)
        value: Any = None
        error: BaseException | None = None
        try:
            value = self.compute(owner)
        except CycleError:
            raise
        except Exception as exc:
            # Cached rather than raised here, so the failure surfaces at every
            # read and the cell can recover on its own -- see below.
            error = exc
        finally:
            _stack.pop()
            self.computing = False
            # Dependencies are rediscovered on every run, so an expression
            # that stopped reading something stops hearing about it.  The ones
            # found before an exception are kept, which is what lets a failed
            # computed recover once the input it was missing arrives.
            for dep in previous:
                if dep not in self.deps:
                    dep.subscribers.discard(self)

        changed = (
            error is not None
            or self.error is not None
            or not self.equal(self.value, value)
        )
        self.value = value
        self.error = error
        self.state = _State.CLEAN
        if changed:
            self.version += 1

    # -- writing --------------------------------------------------------------

    def set(self, value: Any) -> None:
        """Assign a new value.  Refused while a binding is driving this cell."""
        _check_writable(self)
        if self.compute is not None:
            raise ReactiveError(
                f"{self.label} is bound to an expression; call "
                f"unbind() first if you mean to take it over"
            )
        if self.error is None and self.equal(self.value, value):
            return
        self.value = value
        self.error = None
        self.version += 1
        self.notify()

    def notify(self) -> None:
        """Mark everything derived from this cell as needing a second look."""
        pending: list[tuple[_Cell, _State]] = [(self, _State.DIRTY)]
        while pending:
            cell, mark = pending.pop()
            for sub in list(cell.subscribers):
                if sub.state >= mark:
                    # Already at least this suspicious, and so is everything
                    # below it -- which is what keeps a burst of writes cheap.
                    continue
                was_clean = sub.state is _State.CLEAN
                sub.state = mark
                sub.schedule()
                if was_clean:
                    pending.append((sub, _State.CHECK))
        with untracked():
            # Untracked because the repaint hook walks the parent chain, and
            # that chain is itself reactive: an effect that assigns must not
            # end up subscribed to the ancestry of whatever it assigned.
            owner = self.owner()
            changed = getattr(owner, "_reactive_changed", None)
            if changed is not None:
                changed(self.name)

    def schedule(self) -> None:
        """Ask to be re-run.  Only effects need to; values wait to be read."""

    def unlink(self) -> None:
        """Detach from the graph, keeping whatever value was last computed."""
        for dep in self.deps:
            dep.subscribers.discard(self)
        self.deps.clear()
        self.compute = None
        self.state = _State.CLEAN


class Effect(_Cell):
    """A reaction that has to happen whether or not anybody reads a value.

    Effects are the only eager part of the graph.  They are queued when a
    dependency changes and run at a point the application chooses -- between
    dispatching a batch of events and painting the frame -- so the work they
    do, rescanning a directory or clamping a scroll position, never happens in
    the middle of a repaint.
    """

    writable = True

    __slots__ = ("order", "scheduled", "scheduler")

    def __init__(
        self,
        owner: object,
        name: str,
        function: Callable[[Any], Any],
        scheduler: Scheduler,
    ):
        super().__init__(owner, name, compute=function)
        self.order = next(_order)
        self.scheduled = False
        self.scheduler = scheduler

    def schedule(self) -> None:
        if self.computing:
            # An effect that assigns something it also reads -- clamping a
            # cursor against the list it just rebuilt -- would otherwise wake
            # itself for ever.  Its own writes are part of the run it is in.
            return
        if not self.scheduled and self.compute is not None and self.owner():
            self.scheduled = True
            self.scheduler.add(self)

    def run(self) -> None:
        """Re-run the reaction now, letting any failure reach the caller."""
        self.scheduled = False
        self._validate()
        if self.error is not None:
            error, self.error = self.error, None
            raise error

    def dispose(self) -> None:
        """Stop reacting.  Safe to call more than once."""
        self.scheduled = False
        self.unlink()


# -- the scheduler ------------------------------------------------------------


class Scheduler:
    """Collects effects whose dependencies changed and drains them in order.

    Within one flush effects run in the order they were declared, which is how
    a panel says "clamp the cursor, then clamp the scroll" simply by declaring
    them that way round.  An effect queued by another effect runs in the next
    pass of the same flush, so one batch of events settles completely before
    the frame is composed.
    """

    def __init__(self, *, max_passes: int = 100):
        self.max_passes = max_passes
        #: Set by the application, so a reaction queued while the loop is
        #: parked on the event queue still gets a chance to run.
        self.wake: Callable[[], None] | None = None
        self._pending: list[tuple[int, weakref.ref[Effect]]] = []

    @property
    def pending(self) -> bool:
        """True if there is queued work waiting for :meth:`flush`."""
        return bool(self._pending)

    def add(self, effect: Effect) -> None:
        self._pending.append((effect.order, weakref.ref(effect)))
        if self.wake is not None:
            self.wake()

    def flush(self) -> None:
        """Run every queued effect, and everything they queue in turn."""
        for _ in range(self.max_passes):
            if not self._pending:
                return
            batch, self._pending = sorted(self._pending), []
            for _, reference in batch:
                reaction = reference()
                if reaction is not None and reaction.scheduled:
                    reaction.run()
        raise CycleError(
            "effects kept rescheduling each other; one of them is probably "
            "assigning something it also reads"
        )

    def clear(self) -> None:
        """Drop queued work without running it.  Tests use this to isolate."""
        for _, reference in self._pending:
            reaction = reference()
            if reaction is not None:
                reaction.scheduled = False
        self._pending.clear()


#: The scheduler effects use unless they are given another one.  The
#: application drains this between dispatching events and painting.
SCHEDULER = Scheduler()


def flush_effects(scheduler: Scheduler | None = None) -> None:
    """Run every effect waiting to react."""
    (scheduler or SCHEDULER).flush()


# -- declarations -------------------------------------------------------------


def _store(obj: object) -> dict[str, Any]:
    """The ``__dict__`` of *obj*, with a better error when there is none."""
    try:
        return obj.__dict__
    except AttributeError:
        raise ReactiveError(
            f"{type(obj).__name__} has no __dict__, so it cannot carry "
            f"reactive attributes; drop its __slots__ or give it one"
        ) from None


def _cells(obj: object) -> dict[str, _Cell]:
    """The cell store belonging to *obj*, created on first use."""
    store = _store(obj)
    cells = store.get(_CELLS)
    if cells is None:
        cells = store[_CELLS] = {}
    return cells


class _Declaration:
    """What the class-level declarations have in common.

    A declaration is shared by every instance and holds nothing that changes;
    everything mutable lives in the per-instance cell it hands out.  Keeping
    those apart is the whole reason two panels can have different widths.
    """

    name: str
    equal: Callable[[Any, Any], bool] | None

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def cell(self, obj: object) -> _Cell:
        cells = _cells(obj)
        cell = cells.get(self.name)
        if cell is None:
            cell = cells[self.name] = self.make(obj)
        return cell

    def make(self, obj: object) -> _Cell:
        raise NotImplementedError


class Reactive(_Declaration, Generic[T]):
    """An attribute that reports its reads and its writes."""

    def __init__(
        self,
        default: T | None = None,
        *,
        factory: Callable[[], T] | None = None,
        equal: Callable[[T, T], bool] | None = None,
    ):
        self.name = "<reactive>"
        self.default = default
        self.factory = factory
        self.equal = equal

    def make(self, obj: object) -> _Cell:
        value = self.factory() if self.factory is not None else self.default
        return _Cell(obj, self.name, value=value, equal=self.equal)

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> Reactive[T]: ...

    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> T: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        return self.cell(obj).get()

    def __set__(self, obj: object, value: T) -> None:
        self.cell(obj).set(value)


class Computed(_Declaration, Generic[T]):
    """An attribute derived from other reactive attributes."""

    def __init__(
        self,
        function: Callable[[Any], T],
        *,
        equal: Callable[[T, T], bool] | None = None,
    ):
        self.function = function
        self.equal = equal
        self.name = getattr(function, "__name__", "<computed>")
        self.__doc__ = function.__doc__

    def make(self, obj: object) -> _Cell:
        return _Cell(obj, self.name, compute=self.function, equal=self.equal)

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> Computed[T]: ...

    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> T: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        return self.cell(obj).get()

    def __set__(self, obj: object, value: T) -> None:
        raise AttributeError(
            f"{type(obj).__name__}.{self.name} is computed; assign what it "
            f"derives from, or declare it reactive and use bind()"
        )


def reactive(
    default: T | None = None,
    *,
    factory: Callable[[], T] | None = None,
    equal: Callable[[T, T], bool] | None = None,
) -> Any:
    """Declare an observable attribute.

    Give *factory* rather than *default* for a mutable value, so instances do
    not end up sharing one.  *equal* decides what counts as a change; the
    default compares with ``==`` and treats an unchanged value as no event.
    """
    return Reactive(default, factory=factory, equal=equal)


def computed(
    function: Callable[[Any], T] | None = None,
    *,
    equal: Callable[[T, T], bool] | None = None,
) -> Any:
    """Declare an attribute derived from others, as a decorator or a call.

    The expression must be pure: it is re-run whenever something it read has
    changed and somebody asks for the result, which may be in the middle of
    painting a frame.
    """
    if function is None:
        return lambda fn: Computed(fn, equal=equal)
    return Computed(function, equal=equal)


# -- runtime bindings ---------------------------------------------------------


def _declaration(obj: object, name: str) -> _Declaration:
    found = getattr(type(obj), name, None)
    if not isinstance(found, _Declaration):
        raise ReactiveError(f"{type(obj).__name__}.{name} is not reactive")
    return found


def bind(
    obj: object,
    name: str,
    expression: Callable[[Any], Any],
    *,
    equal: Callable[[Any, Any], bool] | None = None,
) -> None:
    """Make *name* on *obj* follow *expression* from now on.

    This is the per-instance half of the system, and the one markup compiles
    to: ``width: parent.width // 2`` becomes a binding on that one widget, not
    a declaration on its class.  Binding again replaces the expression, but a
    plain assignment while a binding is live is an error rather than a silent
    override -- call :func:`unbind` to take the attribute back by hand.
    """
    declaration = _declaration(obj, name)
    if not isinstance(declaration, Reactive):
        raise ReactiveError(
            f"only a reactive attribute can be bound, and "
            f"{type(obj).__name__}.{name} is not one"
        )
    cell = declaration.cell(obj)
    cell.unlink()
    cell.compute = expression
    cell.equal = equal or declaration.equal or _equal
    cell.state = _State.DIRTY
    cell.notify()


def unbind(obj: object, name: str) -> None:
    """Detach the binding on *name*, keeping the value it last produced."""
    cell = _declaration(obj, name).cell(obj)
    with untracked(), contextlib.suppress(Exception):
        cell._validate()
    cell.error = None
    cell.unlink()


def is_bound(obj: object, name: str) -> bool:
    """True if *name* currently derives its value from an expression."""
    return _declaration(obj, name).cell(obj).compute is not None


def peek(obj: object, name: str) -> Any:
    """Read *name* without subscribing to it.

    What an effect uses to look at the value it is about to assign, so that
    assigning does not wake it up again.
    """
    with untracked():
        return getattr(obj, name)


def effect(
    obj: object,
    function: Callable[[Any], Any],
    *,
    immediate: bool = True,
    scheduler: Scheduler | None = None,
) -> Effect:
    """React to changes with something a computed is not allowed to do.

    *function* is called with *obj* and may assign reactive attributes, read
    the filesystem, or anything else with a side effect.  It runs once now --
    which is also how its dependencies are discovered -- and afterwards
    whenever one of them changes, at the next flush rather than immediately.

    The returned handle can be disposed; until then the effect lives exactly
    as long as *obj* does.
    """
    name = getattr(function, "__name__", "<effect>")
    reaction = Effect(obj, name, function, scheduler or SCHEDULER)
    _store(obj).setdefault(_EFFECTS, []).append(reaction)
    if immediate:
        reaction.run()
    else:
        reaction.schedule()
    return reaction
