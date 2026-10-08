"""navkit's run-time key tables: override_keys, restore_keys, default_keys, own_keys."""

from __future__ import annotations

import pytest

from navkit.commands import (
    Command,
    KeyTableError,
    check_table,
    default_keys,
    key_table,
    override_keys,
    own_keys,
    restore_keys,
)
from navkit.widget import Widget


class Save(Command):
    pass


class Close(Command):
    pass


class Open(Command):
    pass


class Base(Widget):
    keys = {"f2": Save, "escape": Close}


class Half(Base):
    keys = {"f3": Open}


class Derived(Half):
    """A component's two halves: Half is the markup's, Derived the hand-written one."""

    keys = {"f4": Close}


class Leaf(Derived):
    keys = {"f5": Save}


@pytest.fixture(autouse=True)
def _clean():
    yield
    restore_keys()


def test_an_override_replaces_what_the_classes_between_bind():
    override_keys(Derived, {"f9": Open}, Half.__mro__[1])
    assert key_table(Derived) == {"f2": Save, "escape": Close, "f9": Open}


def test_an_override_can_take_a_key_away():
    override_keys(Derived, {}, Base)
    assert key_table(Derived) == {"f2": Save, "escape": Close}


def test_a_subclass_without_one_adds_its_own_keys_over_it():
    override_keys(Derived, {"f9": Open}, Base)
    assert key_table(Leaf) == {"f2": Save, "escape": Close, "f9": Open, "f5": Save}


def test_a_base_override_shows_through_a_derived_one():
    override_keys(Base, {"f12": Close}, Widget)
    override_keys(Derived, {"f9": Open}, Base)
    assert key_table(Derived) == {"f12": Close, "f9": Open}


def test_restore_puts_the_code_back():
    override_keys(Derived, {}, Base)
    restore_keys(Derived)
    assert key_table(Derived) == {"f2": Save, "escape": Close, "f3": Open, "f4": Close}


def test_default_and_own_keys():
    assert default_keys(Derived, Base) == {"f3": Open, "f4": Close}
    assert own_keys(Derived, Base) == {"f3": Open, "f4": Close}
    override_keys(Derived, {"f9": Open}, Base)
    assert own_keys(Derived, Base) == {"f9": Open}
    assert default_keys(Derived, Base) == {"f3": Open, "f4": Close}


def test_an_override_is_checked():
    with pytest.raises(KeyTableError):
        override_keys(Derived, {"cmd+s": Save}, Base)
    with pytest.raises(KeyTableError):
        override_keys(Derived, {"ctrl+k": Save, "ctrl+k b": Open}, Base)
    with pytest.raises(KeyTableError):
        override_keys(Derived, {"f2": Save}, Leaf)


def test_check_table_answers_canonical_keys():
    assert check_table("T", {"Ctrl+R": Save, "ctrl+k B": Open}) == {"ctrl+r": Save, "ctrl+k b": Open}
    with pytest.raises(KeyTableError):
        check_table("T", {"Ctrl+R": Save, "ctrl+r": Open})
