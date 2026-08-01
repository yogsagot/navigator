"""The widget tree: parenting, geometry and event dispatch."""

from __future__ import annotations

from navkit.application import Application
from navkit.events import KeyEvent, MouseEvent
from navkit.reactive import bind
from navkit.screen import ScreenBuffer
from navkit.style import Style
from navkit.widget import Widget

from conftest import RecordingWidget, run_app


def test_add_sets_the_parent():
    parent, child = Widget(), Widget()
    assert parent.add(child) is child
    assert child.parent is parent
    assert parent.children == [child]


def test_adding_to_a_new_parent_reparents():
    first, second, child = Widget(), Widget(), Widget()
    first.add(child)
    second.add(child)
    assert first.children == []
    assert second.children == [child]
    assert child.parent is second


def test_constructor_parent_adds_to_the_tree():
    parent = Widget()
    child = Widget(parent=parent)
    assert parent.children == [child]


def test_remove():
    parent, child = Widget(), Widget()
    parent.add(child)
    parent.remove(child)
    assert parent.children == []
    assert child.parent is None


def test_remove_ignores_a_stranger():
    parent = Widget()
    parent.remove(Widget())  # must not raise
    assert parent.children == []


def test_contains():
    widget = Widget(x=2, y=3, width=4, height=2)
    assert widget.contains(2, 3)
    assert widget.contains(5, 4)
    assert not widget.contains(1, 3)
    assert not widget.contains(6, 3)
    assert not widget.contains(2, 5)


def test_layout_cascades_to_children():
    parent = Widget()
    child = parent.add(Widget())
    parent.layout(20, 10)
    assert (parent.width, parent.height) == (20, 10)
    assert (child.width, child.height) == (20, 10)


def test_render_tree_paints_children_over_the_parent():
    parent = RecordingWidget(fill="-", width=4, height=1)
    parent.add(RecordingWidget(fill="#", x=1, width=2, height=1))
    buffer = ScreenBuffer(4, 1)
    parent.render_tree(buffer)
    assert "".join(buffer.get(x, 0)[0] for x in range(4)) == "-##-"


def test_invisible_widgets_and_their_children_are_skipped():
    parent = RecordingWidget(fill="-", width=4, height=1)
    child = parent.add(RecordingWidget(fill="#", width=4, height=1))
    parent.visible = False
    parent.render_tree(ScreenBuffer(4, 1))
    assert (parent.renders, child.renders) == (0, 0)


def test_keys_reach_the_topmost_child_first():
    parent = RecordingWidget()
    lower = parent.add(RecordingWidget())
    upper = parent.add(RecordingWidget())
    assert parent.dispatch_key(KeyEvent("a")) is True
    assert upper.keys == ["a"]
    assert lower.keys == []
    assert parent.keys == []


def test_unhandled_keys_fall_through_to_the_parent():
    parent = RecordingWidget()
    child = parent.add(RecordingWidget())
    child.handles = False
    parent.dispatch_key(KeyEvent("a"))
    assert child.keys == ["a"]
    assert parent.keys == ["a"]


def test_mouse_goes_to_the_widget_under_the_pointer():
    parent = RecordingWidget(width=10, height=10)
    left = parent.add(RecordingWidget(x=0, width=5, height=10))
    right = parent.add(RecordingWidget(x=5, width=5, height=10))
    parent.dispatch_mouse(MouseEvent(7, 2, "left"))
    assert right.mice == [(7, 2)]
    assert left.mice == []


def test_mouse_outside_every_child_lands_on_the_parent():
    parent = RecordingWidget(width=10, height=10)
    child = parent.add(RecordingWidget(x=0, width=2, height=2))
    parent.dispatch_mouse(MouseEvent(8, 8, "left"))
    assert child.mice == []
    assert parent.mice == [(8, 8)]


def test_default_widget_handles_nothing():
    widget = Widget()
    assert widget.on_key(KeyEvent("a")) is False
    assert widget.on_mouse(MouseEvent(0, 0)) is False


def test_application_is_none_outside_a_running_app():
    child = Widget(parent=Widget())
    assert child.application is None
    child.invalidate()  # must not raise


def test_widgets_keep_their_style():
    style = Style(fg=1)
    assert Widget(style=style).style is style

def test_changing_the_geometry_asks_for_a_repaint(terminal):
    root = RecordingWidget()
    app = Application(root, terminal=terminal)
    run_app(app, [lambda a: setattr(root, "x", 3)])
    # The initial paint, then one more because moving the widget dirtied it.
    assert root.renders == 2


def test_a_style_assigned_the_same_value_asks_for_no_repaint(terminal):
    style = Style(fg=1)
    root = RecordingWidget(style=style)
    app = Application(root, terminal=terminal)
    run_app(app, [lambda a: setattr(root, "style", Style(fg=1))])
    assert root.renders == 1  # an equal style is not a change


def test_layout_does_not_overwrite_a_bound_size():
    parent = Widget()
    child = parent.add(Widget())
    bind(child, "width", lambda w: w.parent.width // 2)
    parent.layout(20, 10)
    assert (child.width, child.height) == (10, 10)


def test_a_bound_child_follows_the_terminal_across_a_resize():
    parent = Widget()
    child = parent.add(Widget())
    bind(child, "width", lambda w: w.parent.width // 2)
    parent.layout(20, 10)
    parent.layout(60, 10)
    assert child.width == 30


def test_reparenting_re_evaluates_a_binding():
    first, second = Widget(width=20), Widget(width=60)
    child = first.add(Widget())
    bind(child, "width", lambda w: w.parent.width // 2)
    assert child.width == 10
    second.add(child)
    assert child.width == 30
