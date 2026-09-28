"""Commands and key tables: what a key asks for, where it goes, and when not."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from navkit.application import Application
from navkit.commands import Command, KeyTableError, key_table, layer_key, parse_key
from navkit.events import KeyEvent
from navkit.widget import Widget

from conftest import awaited, run_app


class Save(Command):
    title = "Save"


class Close(Command):
    title = "Close"


@dataclass(frozen=True, slots=True)
class Jump(Command):
    title = "Jump"

    to: int = 0


class Recorder(Widget):
    """Handles Save and Close, and remembers the keys its on_key saw."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ran: list[Command] = []
        self.keys_seen: list[str] = []
        self.allow = True

    def enables(self, command):
        return self.allow

    async def on_save(self, event):
        self.ran.append(event)
        return True

    async def on_close(self, event):
        self.ran.append(event)
        return True

    async def on_key(self, event):
        self.keys_seen.append(event.name)
        return False


class Editor(Recorder):
    keys = {"ctrl+s": Save, "F4": Close}


def tree(root_cls=Widget, child_cls=Recorder):
    """A root and one focused child, attached to an application."""
    root = root_cls()
    child = root.add(child_cls())
    app = Application(root=root)
    child.can_focus = True
    child.focus()
    return app, root, child


# -- the table ------------------------------------------------------------------


def test_a_key_spec_is_read_in_its_canonical_spelling():
    assert parse_key("Shift+Ctrl+F6") == "ctrl+shift+f6"
    for bad in ("", "ctrl+", "ctrl", "cmd+s", "ctrl + s", "+s"):
        with pytest.raises(ValueError):
            parse_key(bad)


def test_tables_merge_down_the_mro_and_the_subclass_wins():
    class Base(Widget):
        keys = {"f2": Save, "f3": Close}

    class Derived(Base):
        keys = {"F3": Save, "f4": Close}

    assert key_table(Derived) == {"f2": Save, "f3": Save, "f4": Close}
    assert key_table(Base) == {"f2": Save, "f3": Close}


@pytest.mark.parametrize(
    ("keys", "message"),
    [
        ({"cmd+s": Save}, "not a key"),
        ({"ctrl+s": Save, "Ctrl+S": Close}, "twice"),
        ({"f2": "save"}, "not a Command"),
        ({"f2": KeyEvent}, "not a Command"),
        ([("f2", Save)], "mapping"),
    ],
)
def test_a_table_that_cannot_mean_anything_is_refused_with_the_class(keys, message):
    with pytest.raises(KeyTableError, match=message):
        type("Broken", (Widget,), {"keys": keys})


# -- a key reaching a table -------------------------------------------------------


def test_a_bound_key_runs_its_command_before_on_key():
    app, root, editor = tree(child_cls=Editor)
    assert awaited(root.dispatch_key(KeyEvent("s", ctrl=True))) is True
    assert editor.ran == [Save()]
    assert editor.keys_seen == []


def test_a_command_starts_at_the_focus_whoever_bound_the_key():
    # The table is the container's; the state the command acts on is the
    # focused widget's, and it is asked first -- Turbo Vision's evCommand.
    class Frame(Widget):
        keys = {"ctrl+s": Save}

    app, frame, child = tree(root_cls=Frame)
    awaited(frame.dispatch_key(KeyEvent("s", ctrl=True)))
    assert child.ran == [Save()]


def test_a_disabled_command_leaves_its_key_to_on_key_and_further_out():
    app, root, editor = tree(child_cls=Editor)
    editor.allow = False
    assert app.command_enabled(Save) is False
    assert awaited(root.dispatch_key(KeyEvent("s", ctrl=True))) is False
    assert editor.ran == []
    assert editor.keys_seen == ["ctrl+s"]


def test_a_command_nobody_handles_is_disabled():
    class Frame(Widget):
        keys = {"f5": Jump}

    app, frame, child = tree(root_cls=Frame)
    assert app.command_enabled(Jump) is False
    assert awaited(frame.dispatch_key(KeyEvent("f5"))) is False


def test_the_nearest_handler_decides_and_its_veto_is_final():
    # A no from the widget nearest the focus is not overruled by a handler
    # further out that would have said yes.
    class Outer(Recorder):
        keys = {"ctrl+s": Save}

    outer = Outer()
    inner = outer.add(Recorder())
    app = Application(root=outer)
    inner.can_focus = True
    inner.focus()
    inner.allow = False
    assert app.command_enabled(Save) is False
    awaited(outer.dispatch_key(KeyEvent("s", ctrl=True)))
    assert (inner.ran, outer.ran) == ([], [])


def test_an_instance_binding_carries_its_field():
    seen = []

    class Frame(Widget):
        keys = {"f5": Jump(to=5), "f6": Jump}

        async def on_jump(self, event):
            seen.append(event.to)
            return True

    app, frame, child = tree(root_cls=Frame)
    awaited(frame.dispatch_key(KeyEvent("f5")))
    awaited(frame.dispatch_key(KeyEvent("f6")))
    assert seen == [5, 0]


# -- the application's table ------------------------------------------------------


class App(Application):
    keys = {"ctrl+q": Close, "f9": Save}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.closed = 0

    async def on_close(self, event):
        self.closed += 1
        return True


def test_the_application_table_runs_before_the_tree(terminal):
    root = Editor()
    root.can_focus = True
    app = App(root, terminal=terminal)
    run_app(app, [lambda a: root.focus(), KeyEvent("q", ctrl=True)])
    # Bound by the application, asked of the focus first: the editor handles
    # Close, so it is the editor's, and the application never sees it.  Its
    # on_key did not see the key either, because the table ran first.
    assert (root.ran, app.closed) == ([Close()], 0)
    assert root.keys_seen == []


def test_a_command_only_the_application_handles_reaches_it(terminal):
    root = Widget()
    app = App(root, terminal=terminal)
    run_app(app, [KeyEvent("q", ctrl=True)])
    assert app.closed == 1


def test_the_application_table_stands_aside_for_a_modal(terminal):
    root = Widget()
    dialog = Recorder()
    dialog.modal = dialog.can_focus = True
    app = App(root, terminal=terminal)
    run_app(app, [lambda a: a.overlay(dialog), KeyEvent("q", ctrl=True)])
    assert app.closed == 0
    assert dialog.keys_seen == ["ctrl+q"]


def test_run_command_is_what_a_key_bar_button_calls():
    app, root, editor = tree(child_cls=Editor)
    assert awaited(app.run_command(Close)) is True
    assert editor.ran == [Close()]


# -- what a key bar reads ---------------------------------------------------------


def test_a_layer_key_is_spelled_the_way_a_table_is_keyed():
    assert layer_key(frozenset(), "f6") == "f6"
    assert layer_key({"shift", "ctrl"}, "f6") == "ctrl+shift+f6"
    assert layer_key(["alt"], "B") == "alt+b"


def test_bindings_are_the_nearest_tables_with_the_applications_on_top():
    class Frame(Widget):
        keys = {"f2": Close, "f4": Save}

    root = Frame()
    editor = root.add(Editor())
    app = App(root=root)
    editor.can_focus = True
    editor.focus()
    found = app.bindings()
    # f4 is the editor's Close, not the frame's Save: the nearer table wins.
    assert found == {"f2": Close(), "f4": Close(), "ctrl+s": Save(),
                     "ctrl+q": Close(), "f9": Save()}


def test_bindings_leave_out_the_application_table_under_a_modal():
    root = Widget()
    app = App(root=root)
    dialog = Editor()
    dialog.modal = True
    app.overlay(dialog)
    assert set(app.bindings()) == {"ctrl+s", "f4"}


def test_enablement_is_reactive_through_what_enables_reads():
    from navkit.reactive import computed, reactive

    class Toggle(Recorder):
        allowed: bool = reactive(True)

        def enables(self, command):
            return self.allowed

    class Probe(Widget):
        @computed
        def can_save(self):
            return self.application.command_enabled(Save)

    root = Probe()
    toggle = root.add(Toggle())
    Application(root=root)
    toggle.can_focus = True
    toggle.focus()
    assert root.can_save is True
    toggle.allowed = False
    assert root.can_save is False
