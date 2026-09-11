"""Observable attributes: tracking, propagation, bindings and effects."""

from __future__ import annotations

import gc
import weakref
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, Optional

import pytest

from navkit.reactive import (
    UNKNOWN,
    Computed,
    CycleError,
    Reactive,
    ReactiveError,
    ReactiveTypeError,
    Scheduler,
    bind,
    computed,
    declarations,
    effect,
    flush_effects,
    is_bound,
    peek,
    reactive,
    runtime_type,
    unbind,
    untracked,
)

if TYPE_CHECKING:
    # Never imported at run time, so an annotation naming it cannot be
    # resolved -- which is one of the cases the declared-type tests cover.
    from decimal import Decimal


class Box:
    """A pair of sources with the derived values a test needs."""

    a = reactive(1)
    b = reactive(2)

    def __init__(self):
        self.runs: list[str] = []

    @computed
    def total(self) -> int:
        """The sum of both sources."""
        self.runs.append("total")
        return self.a + self.b

    @computed
    def doubled(self) -> int:
        self.runs.append("doubled")
        return self.total * 2


# -- per-instance state -------------------------------------------------------


def test_each_instance_keeps_its_own_value():
    first, second = Box(), Box()
    second.a = 100
    assert (first.a, second.a) == (1, 100)


def test_a_computed_is_memoised_per_instance():
    first, second = Box(), Box()
    second.a = 100
    assert (first.total, second.total) == (3, 102)


def test_a_mutable_default_is_built_once_per_instance():
    class Listy:
        items = reactive(factory=list)

    first, second = Listy(), Listy()
    first.items.append("x")
    assert second.items == []


def test_a_class_without_a_dict_cannot_carry_reactive_attributes():
    class Slotted:
        __slots__ = ()
        n = reactive(0)

    with pytest.raises(ReactiveError, match="__dict__"):
        Slotted().n


# -- laziness and memoisation -------------------------------------------------


def test_a_computed_is_not_run_until_it_is_read():
    box = Box()
    box.a = 5
    assert box.runs == []


def test_reading_a_computed_twice_runs_it_once():
    box = Box()
    box.total, box.total
    assert box.runs == ["total"]


def test_a_computed_is_run_again_after_its_source_changes():
    box = Box()
    assert box.total == 3
    box.a = 5
    assert box.total == 7


def test_a_computed_may_read_another_computed():
    box = Box()
    assert box.doubled == 6
    box.b = 4
    assert box.doubled == 10


# -- glitch freedom -----------------------------------------------------------


class Diamond:
    """One source feeding two branches that meet again at the bottom."""

    n = reactive(1)

    def __init__(self):
        self.runs = 0

    left = computed(lambda self: self.n + 1)
    right = computed(lambda self: self.n * 2)

    @computed
    def bottom(self) -> int:
        self.runs += 1
        return self.left + self.right


def test_a_diamond_dependency_recomputes_the_bottom_once():
    diamond = Diamond()
    diamond.bottom
    diamond.runs = 0
    diamond.n = 4
    diamond.bottom
    assert diamond.runs == 1


def test_a_diamond_dependency_never_yields_a_half_updated_value():
    diamond = Diamond()
    diamond.n = 4
    assert diamond.bottom == 13  # (4 + 1) + (4 * 2), both from the same n


# -- the equality guard -------------------------------------------------------


def test_assigning_an_equal_value_notifies_nobody():
    box = Box()
    assert box.total == 3
    box.runs.clear()
    box.a = 1
    assert box.total == 3
    assert box.runs == []


def test_a_computed_that_returns_an_equal_value_stops_the_propagation():
    class Clamped:
        n = reactive(1)

        def __init__(self):
            self.runs = 0

        capped = computed(lambda self: min(self.n, 3))

        @computed
        def below(self) -> int:
            self.runs += 1
            return self.capped * 10

    clamped = Clamped()
    clamped.n = 5
    assert clamped.below == 30
    clamped.runs = 0
    clamped.n = 7  # capped is still 3, so nothing below it can have moved
    assert clamped.below == 30
    assert clamped.runs == 0


def test_a_custom_equality_predicate_is_honoured():
    class Rounded:
        n = reactive(0.0, equal=lambda old, new: round(old) == round(new))

        def __init__(self):
            self.runs = 0

        @computed
        def doubled(self) -> float:
            self.runs += 1
            return self.n * 2

    rounded = Rounded()
    rounded.doubled
    rounded.n = 0.1  # rounds to the same integer, so it is not a change
    rounded.doubled
    assert rounded.runs == 1


# -- the tracking stack -------------------------------------------------------


def test_an_outer_computed_still_tracks_reads_made_after_an_inner_one():
    class Nested:
        a = reactive(1)
        b = reactive(10)

        inner = computed(lambda self: self.a)

        @computed
        def outer(self) -> int:
            return self.inner + self.b  # b is read after inner returns

    nested = Nested()
    assert nested.outer == 11
    nested.b = 20
    assert nested.outer == 21


def test_untracked_reads_create_no_dependency():
    class Quiet:
        a = reactive(1)

        def __init__(self):
            self.runs = 0

        @computed
        def shy(self) -> int:
            self.runs += 1
            with untracked():
                return self.a

    quiet = Quiet()
    assert quiet.shy == 1
    quiet.a = 5
    assert quiet.shy == 1  # still the memoised value
    assert quiet.runs == 1


def test_untracked_nests_inside_a_tracked_computation():
    class Mixed:
        a = reactive(1)
        b = reactive(10)

        @computed
        def some(self) -> int:
            with untracked():
                hidden = self.a
            return hidden + self.b  # tracking resumes for b

    mixed = Mixed()
    assert mixed.some == 11
    mixed.a = 100
    assert mixed.some == 11
    mixed.b = 20
    assert mixed.some == 120


def test_peek_reads_without_subscribing():
    class Quiet:
        a = reactive(1)
        shy = computed(lambda self: peek(self, Quiet.a))

    quiet = Quiet()
    assert quiet.shy == 1
    quiet.a = 5
    assert quiet.shy == 1


# -- dynamic dependencies -----------------------------------------------------


def test_a_dependency_that_is_no_longer_read_stops_triggering_recomputation():
    class Branch:
        flag = reactive(True)
        a = reactive(1)
        b = reactive(2)

        def __init__(self):
            self.runs = 0

        @computed
        def chosen(self) -> int:
            self.runs += 1
            return self.a if self.flag else self.b

    branch = Branch()
    assert branch.chosen == 1
    branch.flag = False
    assert branch.chosen == 2
    branch.runs = 0
    branch.a = 99  # the true branch is no longer taken
    assert branch.chosen == 2
    assert branch.runs == 0


# -- cycles -------------------------------------------------------------------


def test_a_computed_that_reads_itself_raises_instead_of_recursing():
    class Snake:
        tail = computed(lambda self: self.tail + 1)

    with pytest.raises(CycleError, match="Snake.tail"):
        Snake().tail


def test_effects_that_keep_rescheduling_each_other_are_reported_as_a_cycle():
    class Pair:
        p = reactive(0)
        q = reactive(0)

    scheduler = Scheduler(max_passes=10)
    pair = Pair()
    effect(pair, lambda s: setattr(s, "q", s.p + 1), scheduler=scheduler)
    effect(pair, lambda s: setattr(s, "p", s.q + 1), scheduler=scheduler)
    with pytest.raises(CycleError):
        flush_effects(scheduler)


# -- errors and purity --------------------------------------------------------


def test_an_exception_inside_a_computed_reaches_the_reader():
    class Broken:
        n = reactive(0)
        ratio = computed(lambda self: 1 / self.n)

    with pytest.raises(ZeroDivisionError):
        Broken().ratio


def test_a_failed_computed_recovers_when_its_dependency_changes():
    class Broken:
        n = reactive(0)
        ratio = computed(lambda self: 1 / self.n)

    broken = Broken()
    with pytest.raises(ZeroDivisionError):
        broken.ratio
    broken.n = 4
    assert broken.ratio == 0.25


def test_a_computed_may_not_assign_a_reactive_attribute():
    class Impure:
        n = reactive(0)
        sneaky = computed(lambda self: setattr(self, "n", 1))

    with pytest.raises(ReactiveError, match="may not assign"):
        Impure().sneaky


def test_a_computed_cannot_be_assigned():
    with pytest.raises(AttributeError, match="is computed"):
        Box().total = 9


def test_a_computed_keeps_its_docstring():
    assert Box.total.__doc__ == "The sum of both sources."


# -- bindings -----------------------------------------------------------------


class Node:
    """The smallest thing that can be sized in terms of its parent."""

    parent = reactive(None)
    width = reactive(0)


def test_a_binding_attached_at_runtime_drives_the_attribute():
    root, child = Node(), Node()
    root.width = 80
    child.parent = root
    child.width = bind(lambda n: n.parent.width // 2)
    assert child.width == 40
    root.width = 100
    assert child.width == 50


def test_only_one_instance_is_affected_by_a_binding():
    root, bound, plain = Node(), Node(), Node()
    root.width = 80
    bound.parent = plain.parent = root
    bound.width = bind(lambda n: n.parent.width // 2)
    assert (bound.width, plain.width) == (40, 0)


def test_a_binding_can_be_assigned_before_the_expression_can_run():
    """The expression is not called until somebody reads the value."""
    child = Node()
    child.width = bind(lambda n: 1 // 0)
    with pytest.raises(ZeroDivisionError):
        child.width


def test_assigning_over_a_binding_raises():
    child = Node()
    child.width = bind(lambda n: 7)
    with pytest.raises(ReactiveError, match="unbind"):
        child.width = 5


def test_unbind_freezes_the_last_value():
    root, child = Node(), Node()
    root.width = 80
    child.parent = root
    child.width = bind(lambda n: n.parent.width // 2)
    assert child.width == 40
    unbind(child, Node.width)
    root.width = 1000
    assert child.width == 40
    child.width = 5  # and the attribute is writable again
    assert child.width == 5


def test_a_rebind_replaces_the_previous_expression():
    child = Node()
    child.width = bind(lambda n: 7)
    child.width = bind(lambda n: 9)
    assert child.width == 9


def test_is_bound_reports_whether_an_expression_is_driving_the_value():
    child = Node()
    assert not is_bound(child, Node.width)
    child.width = bind(lambda n: 7)
    assert is_bound(child, Node.width)
    unbind(child, Node.width)
    assert not is_bound(child, Node.width)


def test_a_binding_is_re_evaluated_when_the_parent_changes():
    first, second, child = Node(), Node(), Node()
    first.width, second.width = 80, 40
    child.parent = first
    child.width = bind(lambda n: n.parent.width // 2)
    assert child.width == 40
    child.parent = second
    assert child.width == 20


def test_a_binding_on_an_orphan_resolves_once_it_is_parented():
    root, child = Node(), Node()
    root.width = 80
    child.width = bind(lambda n: n.parent.width // 2)
    with pytest.raises(AttributeError):
        child.width
    child.parent = root
    assert child.width == 40


def test_only_a_reactive_attribute_can_be_bound():
    with pytest.raises(AttributeError, match="computed"):
        Box().total = bind(lambda b: 1)


def test_an_attribute_has_to_be_named_by_the_declaration_itself():
    with pytest.raises(ReactiveError, match="not a reactive attribute"):
        is_bound(Node(), "width")  # the name, rather than the attribute
    with pytest.raises(ReactiveError, match="does not declare"):
        is_bound(Node(), Box.a)  # somebody else's attribute


def test_is_bound_refuses_a_computed():
    # A computed's cell always carries a compute, so the question is a
    # category error rather than a question with the answer True.
    with pytest.raises(ReactiveError, match="computed, not bound"):
        is_bound(Box(), Box.total)


def test_unbind_refuses_a_computed_rather_than_freezing_it():
    box = Box()
    assert box.total == 3
    with pytest.raises(ReactiveError, match="computed, not bound"):
        unbind(box, Box.total)
    # Unlinking the cell would have left it answering 3 for ever.
    box.a = 10
    assert box.total == 12


def test_peek_still_reads_a_computed():
    # Only the two that talk about bindings refuse one; peeking a derived
    # value without subscribing to it stays legitimate.
    box = Box()
    assert peek(box, Box.total) == 3


def test_a_computed_may_not_install_a_binding():
    class Sneak:
        a = reactive(1)
        target = reactive(0)

        @computed
        def impure(self) -> int:
            self.target = bind(lambda s: 5)
            return self.a

    with pytest.raises(ReactiveError, match="may not assign"):
        Sneak().impure


# -- effects ------------------------------------------------------------------


class Counter:
    """A source and an effect that records every value it saw."""

    n = reactive(0)

    def __init__(self):
        self.seen: list[int] = []

    def watch(self) -> None:
        self.seen.append(self.n)


def test_an_effect_runs_once_when_it_is_created():
    counter = Counter()
    effect(counter, Counter.watch)
    assert counter.seen == [0]


def test_an_effect_does_not_run_again_until_the_scheduler_is_flushed():
    scheduler = Scheduler()
    counter = Counter()
    effect(counter, Counter.watch, scheduler=scheduler)
    counter.n = 1
    assert counter.seen == [0]
    flush_effects(scheduler)
    assert counter.seen == [0, 1]


def test_a_burst_of_writes_runs_an_effect_once():
    scheduler = Scheduler()
    counter = Counter()
    effect(counter, Counter.watch, scheduler=scheduler)
    counter.n = 1
    counter.n = 2
    counter.n = 3
    flush_effects(scheduler)
    assert counter.seen == [0, 3]


def test_effects_run_in_the_order_they_were_declared():
    class Both:
        n = reactive(0)

        def __init__(self):
            self.order: list[str] = []

    scheduler = Scheduler()
    both = Both()
    effect(both, lambda s: (s.n, s.order.append("first")), scheduler=scheduler)
    effect(both, lambda s: (s.n, s.order.append("second")), scheduler=scheduler)
    both.order.clear()
    both.n = 1
    flush_effects(scheduler)
    assert both.order == ["first", "second"]


def test_an_effect_scheduled_by_another_effect_runs_in_the_same_flush():
    class Chain:
        a = reactive(0)
        b = reactive(0)

        def __init__(self):
            self.seen: list[int] = []

    scheduler = Scheduler()
    chain = Chain()
    effect(chain, lambda s: setattr(s, "b", s.a * 2), scheduler=scheduler)
    effect(chain, lambda s: s.seen.append(s.b), scheduler=scheduler)
    chain.seen.clear()
    chain.a = 5
    flush_effects(scheduler)
    assert chain.seen == [10]


def test_an_effect_may_assign_something_it_reads_without_re_running_itself():
    class Clamp:
        cursor = reactive(0)

        def __init__(self):
            self.runs = 0

        def clamp(self) -> None:
            self.runs += 1
            self.cursor = min(self.cursor, 3)

    scheduler = Scheduler()
    clamp = Clamp()
    effect(clamp, Clamp.clamp, scheduler=scheduler)
    clamp.cursor = 10
    flush_effects(scheduler)
    assert (clamp.cursor, clamp.runs) == (3, 2)


def test_a_disposed_effect_stops_running():
    scheduler = Scheduler()
    counter = Counter()
    handle = effect(counter, Counter.watch, scheduler=scheduler)
    handle.dispose()
    counter.n = 1
    flush_effects(scheduler)
    assert counter.seen == [0]


def test_an_effect_can_be_created_without_running_it():
    scheduler = Scheduler()
    counter = Counter()
    effect(counter, Counter.watch, immediate=False, scheduler=scheduler)
    assert counter.seen == []
    flush_effects(scheduler)
    assert counter.seen == [0]


def test_a_failing_effect_reaches_the_caller_of_flush():
    scheduler = Scheduler()
    counter = Counter()
    effect(counter, Counter.watch, scheduler=scheduler)

    def boom(_: Counter) -> None:
        raise ValueError("no")

    effect(counter, boom, immediate=False, scheduler=scheduler)
    with pytest.raises(ValueError):
        flush_effects(scheduler)


# -- lifetimes ----------------------------------------------------------------


def test_a_dependent_is_collected_even_though_its_source_saw_it():
    root, child = Node(), Node()
    root.width = 80
    child.parent = root
    child.width = bind(lambda n: n.parent.width // 2)
    assert child.width == 40

    reference = weakref.ref(child)
    del child
    gc.collect()
    assert reference() is None


def test_a_collected_subscriber_does_not_break_a_later_write():
    root, child = Node(), Node()
    root.width = 80
    child.parent = root
    child.width = bind(lambda n: n.parent.width // 2)
    child.width
    del child
    gc.collect()
    root.width = 100  # must not raise
    assert root.width == 100


def test_an_effect_on_a_collected_owner_is_skipped_by_the_flush():
    scheduler = Scheduler()
    counter = Counter()
    effect(counter, Counter.watch, scheduler=scheduler)
    counter.n = 1
    del counter
    gc.collect()
    flush_effects(scheduler)  # must not raise
    assert not scheduler.pending


# -- declarations -------------------------------------------------------------


class Base:
    """Two sources and a derived value, for the declaration walk."""

    width = reactive(0)
    height = reactive(0)
    plain = "not reactive"

    @computed
    def area(self) -> int:
        return self.width * self.height


class Derived(Base):
    depth = reactive(0)


def test_declarations_finds_the_attributes_a_class_declares():
    assert set(declarations(Base)) == {"width", "height", "area"}


def test_declarations_includes_inherited_attributes():
    assert set(declarations(Derived)) == {"width", "height", "area", "depth"}


def test_declarations_tells_a_source_from_a_derived_value():
    found = declarations(Base)
    assert isinstance(found["width"], Reactive)
    assert isinstance(found["area"], Computed)


def test_declarations_leaves_out_a_plain_attribute():
    assert "plain" not in declarations(Base)


def test_an_override_wins_over_the_declaration_it_shadows():
    class Overriding(Base):
        width = reactive(80)

    assert declarations(Overriding)["width"] is Overriding.width
    assert declarations(Overriding)["width"] is not Base.width


def test_declarations_maps_each_name_to_the_class_attribute_itself():
    # What `unbind`, `is_bound` and `peek` take, so a generator can hand the
    # declaration straight on rather than looking it up again by name.
    assert declarations(Base)["width"] is Base.__dict__["width"]


def test_declarations_of_a_class_with_none_is_empty():
    class Bare:
        pass

    assert declarations(Bare) == {}


# -- declared types -----------------------------------------------------------


class Typed:
    """One attribute per shape the declared-type check has to tell apart."""

    count: int = reactive(0)
    label: str = reactive("")
    tags: frozenset[str] = reactive(frozenset())
    maybe: str | None = reactive(None)
    anything: Any = reactive(None)
    unannotated = reactive(0)
    #: Resolvable only under a type checker, so unchecked at run time.
    absent: Decimal | None = reactive(None)


def test_a_value_of_the_declared_type_is_stored():
    typed = Typed()
    typed.count = 5
    assert typed.count == 5


def test_a_value_contradicting_the_declared_type_is_refused():
    typed = Typed()
    with pytest.raises(ReactiveTypeError):
        typed.count = "five"
    assert typed.count == 0


def test_the_refusal_is_also_a_type_error():
    # Both bases, so either `except` catches it.
    typed = Typed()
    with pytest.raises(TypeError):
        typed.count = "five"
    with pytest.raises(ReactiveError):
        typed.count = "five"


def test_the_refusal_names_the_attribute_and_both_types():
    typed = Typed()
    with pytest.raises(ReactiveTypeError) as raised:
        typed.count = "five"
    message = str(raised.value)
    assert "Typed.count" in message
    assert "int" in message
    assert "str" in message


def test_none_is_refused_where_the_declared_type_does_not_admit_it():
    typed = Typed()
    with pytest.raises(ReactiveTypeError):
        typed.count = None


def test_every_arm_of_a_union_is_accepted():
    typed = Typed()
    typed.maybe = "here"
    assert typed.maybe == "here"
    typed.maybe = None
    assert typed.maybe is None
    with pytest.raises(ReactiveTypeError):
        typed.maybe = 3


def test_a_subclass_of_the_declared_type_is_accepted():
    class Longer(str):
        pass

    typed = Typed()
    typed.label = Longer("wide")
    assert typed.label == "wide"


def test_only_the_container_is_checked_not_what_is_in_it():
    # The erasure is deliberately shallow: checking the elements would mean
    # walking every collection on every write.
    typed = Typed()
    typed.tags = frozenset({1, 2})
    assert typed.tags == frozenset({1, 2})
    with pytest.raises(ReactiveTypeError):
        typed.tags = {"a"}  # a set is not a frozenset


def test_an_attribute_declared_any_takes_anything():
    typed = Typed()
    typed.anything = object()
    typed.anything = None


def test_an_unannotated_attribute_takes_anything():
    # Opting out is the same act as never opting in, which is why there is
    # no flag for it.
    typed = Typed()
    typed.unannotated = "not an int at all"
    assert typed.unannotated == "not an int at all"


def test_a_type_that_does_not_exist_at_run_time_is_unchecked():
    # `Decimal` is imported under TYPE_CHECKING, so the annotation cannot be
    # evaluated here -- which is a fact about the annotation, not an error.
    typed = Typed()
    typed.absent = "whatever"
    assert typed.absent == "whatever"


def test_one_unresolvable_annotation_does_not_disarm_the_others():
    # What `typing.get_type_hints()` would have done to this whole class.
    assert Typed.count.check is int
    assert Typed.absent.check is None


def test_a_contradicting_write_is_refused_even_when_it_compares_equal():
    typed = Typed()
    with pytest.raises(ReactiveTypeError):
        typed.count = 0.0  # == 0, and still not an int


def test_an_attribute_may_be_declared_with_the_class_being_defined():
    # Resolved on first ask rather than in `__set_name__`, which runs while
    # the class body is still executing.  Declared inside a function, so the
    # name never becomes a module global and only the class itself resolves it.
    class Tree:
        parent: Tree | None = reactive(None)

    root, child = Tree(), Tree()
    child.parent = root
    assert child.parent is root
    with pytest.raises(ReactiveTypeError):
        child.parent = "not a tree"


def test_a_redeclared_attribute_inherits_the_type_it_was_annotated_with():
    class Narrower(Typed):
        count = reactive(1)  # no annotation of its own

    narrower = Narrower()
    assert Narrower.__dict__["count"].check is int
    with pytest.raises(ReactiveTypeError):
        narrower.count = "five"


def test_a_declared_type_is_resolved_once():
    class Once:
        n: int = reactive(0)

    declaration = Once.__dict__["n"]
    assert declaration.type is declaration.type
    assert declaration.check is declaration.check


def test_a_binding_may_produce_a_value_of_any_type():
    # The check guards the boundary where a value enters the graph from
    # outside; what an expression computes came from values that were checked.
    typed = Typed()
    typed.count = bind(lambda _: "not an int")
    assert typed.count == "not an int"


def test_a_bound_attribute_says_it_is_bound_rather_than_reporting_the_type():
    # Correcting the type would not make the assignment legal, so the guard
    # that blocks every value alike is the one that should speak.
    typed = Typed()
    typed.count = bind(lambda _: 1)
    with pytest.raises(ReactiveError) as raised:
        typed.count = "five"
    assert "bound" in str(raised.value)
    assert not isinstance(raised.value, ReactiveTypeError)


def test_a_declared_default_is_not_checked():
    # It is written three characters from the annotation and a type checker
    # catches it there; the run-time check is for values arriving later.
    class Wrong:
        n: int = reactive("zero")

    assert Wrong().n == "zero"


# -- erasing a declared type --------------------------------------------------


type Color = int | tuple[int, int, int]


def test_runtime_type_leaves_a_plain_class_alone():
    assert runtime_type(int) is int


def test_runtime_type_erases_a_parameterised_container_to_the_container():
    assert runtime_type(list[str]) is list
    assert runtime_type(dict[str, int]) is dict


def test_runtime_type_flattens_a_union_into_a_tuple():
    assert runtime_type(str | None) == (str, type(None))
    assert runtime_type(Optional[str]) == (str, type(None))
    assert runtime_type(list[int] | str) == (list, str)


def test_runtime_type_unwraps_a_type_alias():
    assert runtime_type(Color) == (int, tuple)


def test_runtime_type_has_nothing_to_check_for_any_or_unknown():
    assert runtime_type(Any) is None
    assert runtime_type(UNKNOWN) is None


def test_one_unconstrained_arm_leaves_the_whole_union_unconstrained():
    assert runtime_type(int | Any) is None


def test_runtime_type_erases_a_callable_to_something_checkable():
    # `isinstance(f, Callable)` is a real question, so the arguments go and
    # the check stays.
    assert runtime_type(Callable[[int], str]) is Callable


def test_runtime_type_gives_up_on_a_form_it_cannot_erase():
    assert runtime_type(Literal["a", "b"]) is None
    assert runtime_type("a string that is not a type") is None


def test_an_arm_that_cannot_be_erased_disarms_the_whole_union():
    # Half-checking a union would refuse values the annotation allows.
    assert runtime_type(Literal[1] | None) is None


def test_unknown_is_not_any():
    # An answer and the absence of one, kept apart for a consumer that cares.
    assert UNKNOWN is not Any
    assert repr(UNKNOWN) == "UNKNOWN"
