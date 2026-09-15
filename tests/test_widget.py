"""The widget tree: parenting, geometry, event dispatch and emitted events."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from navkit.application import Application
from navkit.events import DoubleClickEvent, Event, KeyEvent, MouseEvent
from navkit.reactive import bind, effect, flush_effects
from navkit.screen import ScreenBuffer
from navkit.style import Style
from navkit.stylesheet import parse
from navkit.widget import Widget

from conftest import RecordingWidget, awaited, run_app


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


def test_keys_go_to_the_focused_widget_and_not_its_siblings():
    parent = RecordingWidget()
    lower = parent.add(RecordingWidget())
    upper = parent.add(RecordingWidget())
    Application(root=parent)
    lower.can_focus = True
    lower.focus()
    assert awaited(parent.dispatch_key(KeyEvent("a"))) is True
    assert lower.keys == ["a"]
    assert upper.keys == []
    assert parent.keys == []


def test_unhandled_keys_fall_through_to_the_parent():
    parent = RecordingWidget()
    child = parent.add(RecordingWidget())
    Application(root=parent)
    child.can_focus = True
    child.focus()
    child.handles = False
    awaited(parent.dispatch_key(KeyEvent("a")))
    assert child.keys == ["a"]
    assert parent.keys == ["a"]


def test_with_nothing_focused_a_key_reaches_nobody_in_the_tree():
    # The old behaviour toured every descendant until one claimed the key.
    # A key belongs to whatever holds the keyboard, and when nothing does,
    # only the widget it was dispatched on is asked.
    parent = RecordingWidget()
    child = parent.add(RecordingWidget())
    Application(root=parent)
    assert awaited(parent.dispatch_key(KeyEvent("a"))) is True
    assert parent.keys == ["a"]
    assert child.keys == []


def test_mouse_goes_to_the_widget_under_the_pointer():
    parent = RecordingWidget(width=10, height=10)
    left = parent.add(RecordingWidget(x=0, width=5, height=10))
    right = parent.add(RecordingWidget(x=5, width=5, height=10))
    awaited(parent.dispatch_mouse(MouseEvent(7, 2, "left")))
    # Column 7 of the parent is column 2 of the right-hand child.
    assert right.mice == [(2, 2)]
    assert left.mice == []


def test_mouse_outside_every_child_lands_on_the_parent():
    parent = RecordingWidget(width=10, height=10)
    child = parent.add(RecordingWidget(x=0, width=2, height=2))
    awaited(parent.dispatch_mouse(MouseEvent(8, 8, "left")))
    assert child.mice == []
    assert parent.mice == [(8, 8)]


def test_default_widget_handles_nothing():
    widget = Widget()
    assert awaited(widget.on_key(KeyEvent("a"))) is False
    assert awaited(widget.on_mouse(MouseEvent(0, 0))) is False


def test_application_is_none_outside_a_running_app():
    child = Widget(parent=Widget())
    assert child.application is None
    child.invalidate()  # must not raise


def test_widgets_keep_their_style():
    style = Style(fg=1)
    # A whole Style inline is the seven declarations it makes, so it resolves
    # back to itself -- there is no stylesheet here to cascade under it.
    assert Widget(inline_style=style).style == style


def test_changing_the_geometry_asks_for_a_repaint(terminal):
    root = RecordingWidget()
    app = Application(root, terminal=terminal)
    run_app(app, [lambda a: setattr(root, "x", 3)])
    # The initial paint, then one more because moving the widget dirtied it.
    assert root.renders == 2


def test_a_style_assigned_the_same_value_asks_for_no_repaint(terminal):
    style = Style(fg=1)
    root = RecordingWidget(inline_style=style)
    app = Application(root, terminal=terminal)
    run_app(app, [lambda a: setattr(root, "inline_style", Style(fg=1))])
    assert root.renders == 1  # an equal style is not a change


def test_layout_does_not_overwrite_a_bound_size():
    parent = Widget()
    child = parent.add(Widget())
    child.width = bind(lambda w: w.parent.width // 2)
    parent.layout(20, 10)
    assert (child.width, child.height) == (10, 10)


def test_a_bound_child_follows_the_terminal_across_a_resize():
    parent = Widget()
    child = parent.add(Widget())
    child.width = bind(lambda w: w.parent.width // 2)
    parent.layout(20, 10)
    parent.layout(60, 10)
    assert child.width == 30


def test_reparenting_re_evaluates_a_binding():
    first, second = Widget(width=20), Widget(width=60)
    child = first.add(Widget())
    child.width = bind(lambda w: w.parent.width // 2)
    assert child.width == 10
    second.add(child)
    assert child.width == 30


def test_a_widget_paints_in_its_own_coordinates():
    class Corner(Widget):
        def render(self, surface):
            surface.draw_text(0, 0, "X")

    root = Widget(width=6, height=2)
    root.add(Corner(x=4, y=1, width=1, height=1))
    buffer = ScreenBuffer(6, 2)
    root.render_tree(buffer)
    # The widget asked for 0, 0 and landed where it was placed.
    assert buffer.get(4, 1)[0] == "X"
    assert buffer.get(0, 0)[0] == " "


def test_a_widget_cannot_paint_outside_itself():
    class Greedy(Widget):
        def render(self, surface):
            surface.fill(-5, -5, 99, 99, "#")

    root = Widget(width=8, height=3)
    root.add(Greedy(x=2, y=1, width=3, height=1))
    buffer = ScreenBuffer(8, 3)
    root.render_tree(buffer)
    rows = ["".join(buffer.get(x, y)[0] for x in range(8)) for y in range(3)]
    assert rows == ["        ", "  ###   ", "        "]


def test_a_grandchild_is_placed_relative_to_its_parent():
    class Dot(Widget):
        def render(self, surface):
            surface.draw_text(0, 0, "*")

    root = Widget(width=10, height=3)
    middle = root.add(Widget(x=3, y=1, width=6, height=2))
    middle.add(Dot(x=2, y=0, width=1, height=1))
    buffer = ScreenBuffer(10, 3)
    root.render_tree(buffer)
    assert buffer.get(5, 1)[0] == "*"  # 3 + 2 across, 1 + 0 down


def test_a_mouse_position_is_relative_to_the_widget_that_handles_it():
    root = RecordingWidget(width=10, height=6)
    middle = root.add(RecordingWidget(x=3, y=1, width=6, height=4))
    leaf = middle.add(RecordingWidget(x=2, y=1, width=2, height=2))
    awaited(root.dispatch_mouse(MouseEvent(6, 3, "left")))
    assert leaf.mice == [(1, 1)]  # 6 - 3 - 2 across, 3 - 1 - 1 down


# -- emitting --------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ClickEvent(Event):
    """A widget's own event, of the kind a button would raise."""

    label: str = ""


class Listener(Widget):
    """Records the clicks it is offered, and claims them on request."""

    def __init__(self, name: str, claims: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.heard: list[str] = []
        self.claims = claims

    async def on_click(self, event: ClickEvent) -> bool:
        self.heard.append(event.label)
        return self.claims


def test_an_emitted_event_starts_at_the_widget_that_raised_it():
    root = Listener("root")
    box = root.add(Listener("box"))
    button = box.add(Listener("button"))
    assert awaited(button.emit(ClickEvent("ok"))) is False
    assert (button.heard, box.heard, root.heard) == (["ok"], ["ok"], ["ok"])


def test_a_claimed_event_stops_where_it_was_claimed():
    root = Listener("root")
    box = root.add(Listener("box", claims=True))
    button = box.add(Listener("button"))
    assert awaited(button.emit(ClickEvent("ok"))) is True
    assert button.heard == ["ok"]
    assert box.heard == ["ok"]
    assert root.heard == []


def test_the_widget_that_emits_gets_first_refusal():
    # What markup compiles to: the handler sits on the block that raises it.
    root = Listener("root")
    button = root.add(Listener("button", claims=True))
    awaited(button.emit(ClickEvent("ok")))
    assert root.heard == []


def test_a_handler_may_be_assigned_onto_the_instance():
    # The shape navml's generated __init__ emits: an async one-argument
    # function under the event's handler name, shadowing the class's.
    root = Widget()
    button = root.add(Widget())
    seen = []

    async def on_click(event):
        seen.append(event.label)
        return True

    button.on_click = on_click
    assert awaited(button.emit(ClickEvent("ok"))) is True
    assert seen == ["ok"]


def test_a_widget_declaring_no_handler_is_skipped():
    # A new event type needs no stub on Widget, or anywhere else.
    root = Widget()
    middle = root.add(Widget())
    button = middle.add(Listener("button"))
    assert awaited(button.emit(ClickEvent("ok"))) is False
    assert button.heard == ["ok"]


def test_a_detached_widget_emits_into_nothing():
    loose = Listener("loose")
    assert awaited(loose.emit(ClickEvent("ok"))) is False
    assert loose.heard == ["ok"]


def test_an_emitted_event_reaches_the_application_after_the_tree():
    class Watching(Application):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.heard: list[str] = []

        async def on_click(self, event: ClickEvent) -> bool:
            self.heard.append(event.label)
            return True

    root = Listener("root")
    button = root.add(Listener("button"))
    app = Watching(root=root)
    assert awaited(button.emit(ClickEvent("ok"))) is True
    assert root.heard == ["ok"]
    assert app.heard == ["ok"]


def test_the_application_on_event_hook_does_not_see_an_emitted_event():
    # on_event exists to intercept an event *before* the widgets; an
    # emitted event has already passed every one of them.
    class Watching(Application):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.intercepted: list[object] = []

        async def on_event(self, event) -> bool:
            self.intercepted.append(event)
            return True

    root = Listener("root")
    app = Watching(root=root)
    awaited(root.emit(ClickEvent("ok")))
    assert app.intercepted == []


def test_a_mouse_press_can_be_turned_into_an_emitted_event_without_focus():
    # The whole of a mouse-driven button, with no focus notion in navkit:
    # dispatch_mouse routes by position, the widget emits from there.
    class Button(Listener):
        async def on_mouse(self, event: MouseEvent) -> bool:
            if event.action == "press":
                return await self.emit(ClickEvent(self.name))
            return False

    root = Listener("root", width=40, height=10)
    box = root.add(Listener("box", x=4, y=2, width=20, height=4))
    button = box.add(Button("ok", x=1, y=1, width=8, height=1))
    awaited(root.dispatch_mouse(MouseEvent(5, 3, "left", "press")))
    assert button.heard == ["ok"]
    assert box.heard == ["ok"]
    assert root.heard == ["ok"]


# -- focus -----------------------------------------------------------------


def test_a_widget_does_not_take_focus_unless_it_says_so():
    # False on the base class: a container, a label and a frame stay out of
    # the tab order by saying nothing at all.
    root = Widget()
    child = root.add(Widget())
    Application(root=root)
    assert child.can_focus is False
    assert child.focus() is False
    assert child.focused is False


def test_focus_moves_the_application_pointer_and_the_state_with_it():
    root = Widget()
    first = root.add(Widget())
    second = root.add(Widget())
    app = Application(root=root)
    first.can_focus = second.can_focus = True

    assert first.focus() is True
    assert (app.focused, first.focused, second.focused) == (first, True, False)
    assert second.focus() is True
    assert (app.focused, first.focused, second.focused) == (second, False, True)


def test_focused_is_a_stylesheet_state():
    # It is a computed, so it is read through the same getattr every :state
    # selector uses -- and moving focus restyles both widgets untold.
    sheet = parse("Widget { bold: false } Widget:focused { bold: true }")
    root = Widget()
    widget = root.add(Widget())
    app = Application(root=root, stylesheet=sheet)
    widget.can_focus = True
    assert widget.style.bold is False
    widget.focus()
    assert widget.style.bold is True
    app.focused = None
    assert widget.style.bold is False


def test_an_invisible_widget_cannot_be_focused():
    root = Widget()
    widget = root.add(Widget())
    Application(root=root)
    widget.can_focus = True
    widget.visible = False
    assert widget.focus() is False


def test_a_detached_widget_cannot_be_focused():
    loose = Widget()
    loose.can_focus = True
    assert loose.focus() is False
    assert loose.focused is False


def test_the_tab_order_is_visible_focusable_widgets_in_tree_order():
    root = Widget()
    first = root.add(Widget())
    box = root.add(Widget())
    second = box.add(Widget())
    third = box.add(Widget())
    skipped = root.add(Widget())
    hidden = root.add(Widget())
    for widget in (first, second, third, hidden):
        widget.can_focus = True
    hidden.visible = False
    assert skipped.can_focus is False
    assert root.focusable() == [first, second, third]


def test_a_container_that_takes_focus_comes_before_its_children():
    root = Widget()
    box = root.add(Widget())
    inner = box.add(Widget())
    box.can_focus = inner.can_focus = True
    assert root.focusable() == [box, inner]


def test_a_subtree_orders_only_itself():
    # What a modal dialog will run: the same walk over its own subtree, with
    # nothing outside it reachable.
    root = Widget()
    outside = root.add(Widget())
    dialog = root.add(Widget())
    inner = dialog.add(Widget())
    outside.can_focus = dialog.can_focus = inner.can_focus = True
    assert dialog.focusable() == [dialog, inner]


def test_focus_next_walks_the_order_and_wraps():
    root = Widget()
    first, second = root.add(Widget()), root.add(Widget())
    app = Application(root=root)
    first.can_focus = second.can_focus = True

    assert app.focus_next() is first
    assert app.focus_next() is second
    assert app.focus_next() is first


def test_focus_next_in_reverse_starts_at_the_end():
    root = Widget()
    first, second = root.add(Widget()), root.add(Widget())
    app = Application(root=root)
    first.can_focus = second.can_focus = True

    assert app.focus_next(reverse=True) is second
    assert app.focus_next(reverse=True) is first
    assert app.focus_next(reverse=True) is second


def test_focus_next_answers_none_when_nothing_can_be_focused():
    root = Widget()
    root.add(Widget())
    app = Application(root=root)
    assert app.focus_next() is None
    assert app.focused is None


def test_tab_out_of_a_widget_that_left_the_order_lands_on_the_first():
    root = Widget()
    first, second = root.add(Widget()), root.add(Widget())
    app = Application(root=root)
    first.can_focus = second.can_focus = True
    second.focus()
    second.visible = False
    assert app.focus_next() is first


def test_removing_the_focused_widget_clears_the_focus():
    root = Widget()
    box = root.add(Widget())
    inner = box.add(Widget())
    app = Application(root=root)
    inner.can_focus = True
    inner.focus()

    # Removing the container it sits in, not the widget itself: focus would
    # otherwise keep pointing into a subtree that is no longer on screen.
    root.remove(box)
    assert app.focused is None
    assert inner.focused is False


def test_removing_an_unrelated_widget_leaves_the_focus_alone():
    root = Widget()
    keeper = root.add(Widget())
    other = root.add(Widget())
    app = Application(root=root)
    keeper.can_focus = True
    keeper.focus()
    root.remove(other)
    assert app.focused is keeper


def test_a_key_is_not_delivered_through_an_invisible_ancestor():
    # Focus is a pointer; whether it can be reached is decided when the key
    # arrives, so hiding a container does not have to chase the focus inside
    # it.  The container itself is offered the key instead.
    root = RecordingWidget()
    box = root.add(RecordingWidget())
    inner = box.add(RecordingWidget())
    Application(root=root)
    inner.can_focus = True
    inner.focus()
    box.visible = False

    awaited(root.dispatch_key(KeyEvent("a")))
    assert inner.keys == []
    assert root.keys == ["a"]


# -- mounting --------------------------------------------------------------


class LifecycleWidget(Widget):
    """Records its own lifecycle, in the order it is told about it."""

    def __init__(self, log: list[str], tag: str, **kwargs):
        super().__init__(**kwargs)
        self.log = log
        self.tag = tag

    def mounted(self) -> None:
        self.log.append(f"mount {self.tag}")

    def unmounting(self) -> None:
        self.log.append(f"unmount {self.tag}")


def test_a_tree_is_not_mounted_until_it_has_an_application():
    log: list[str] = []
    root = LifecycleWidget(log, "root")
    root.add(LifecycleWidget(log, "child"))
    assert log == []
    assert root.is_mounted is False

    Application(root=root)
    assert log == ["mount root", "mount child"]
    assert root.is_mounted is True


def test_mounting_goes_parents_first_and_unmounting_children_first():
    log: list[str] = []
    root = LifecycleWidget(log, "root")
    box = root.add(LifecycleWidget(log, "box"))
    box.add(LifecycleWidget(log, "inner"))
    app = Application(root=root)
    assert log == ["mount root", "mount box", "mount inner"]

    log.clear()
    app.root = None
    assert log == ["unmount inner", "unmount box", "unmount root"]


def test_adding_to_a_mounted_widget_mounts_the_new_subtree():
    log: list[str] = []
    root = LifecycleWidget(log, "root")
    Application(root=root)
    log.clear()

    box = LifecycleWidget(log, "box")
    box.add(LifecycleWidget(log, "inner"))
    root.add(box)
    assert log == ["mount box", "mount inner"]
    assert box.is_mounted is True


def test_a_mount_handler_sees_a_settled_geometry_and_an_application():
    seen = {}

    class Probe(Widget):
        def mounted(self) -> None:
            seen["size"] = (self.width, self.height)
            seen["app"] = self.application is not None

    root = Widget()
    root.add(Probe())
    Application(root=root, terminal=None)
    assert seen["app"] is True
    assert seen["size"] == (root.width, root.height)


def test_an_unmount_handler_still_has_its_place():
    seen = {}

    class Probe(Widget):
        def unmounting(self) -> None:
            seen["parent"] = self.parent
            seen["mounted"] = self.is_mounted

    root = Widget()
    probe = root.add(Probe())
    Application(root=root)
    root.remove(probe)
    assert seen["parent"] is root
    assert seen["mounted"] is True
    assert probe.is_mounted is False


def test_a_widget_added_to_a_running_tree_is_laid_out():
    # Without this it is 0x0 until the next terminal resize, and a dialog
    # opened at run time paints nothing at all -- silently.
    root = Widget()
    Application(root=root)
    root.width, root.height = 40, 10
    child = root.add(Widget())
    assert (child.width, child.height) == (40, 10)


def test_adding_to_an_unattached_tree_does_not_touch_the_size():
    # layout() hands the parent's size to every unbound child, so laying out
    # at add() time would overwrite a width the caller just passed in.
    parent = Widget(width=10, height=10)
    child = parent.add(Widget(width=2, height=2))
    assert (child.width, child.height) == (2, 2)


def test_removing_a_widget_disposes_the_effects_it_registered():
    root = Widget()
    probe = root.add(Widget())
    Application(root=root)
    runs = []
    effect(probe, lambda w: runs.append(w.width))
    assert len(runs) == 1

    root.remove(probe)
    probe.width = probe.width + 7
    flush_effects()
    assert len(runs) == 1


def test_an_effect_reading_the_parent_does_not_take_the_application_down():
    # The failure the lifecycle exists for: an effect is eager, so the very
    # write that detaches the widget queues it, and it raises at the next
    # flush -- which Application turns into an exit and a re-raise.
    root = Widget()
    probe = root.add(Widget())
    Application(root=root)
    widths = []
    effect(probe, lambda w: widths.append(w.parent.width))
    assert len(widths) == 1

    root.remove(probe)
    flush_effects()  # would raise AttributeError without the disposal
    assert len(widths) == 1


def test_effects_registered_on_mount_come_back_when_it_is_mounted_again():
    # The contract disposal buys: a widget that can be detached declares its
    # effects in on_mount, and gets a live set every time it is put back.
    runs = []

    class Probe(Widget):
        def mounted(self) -> None:
            effect(self, lambda w: runs.append(w.width))

    root = Widget()
    probe = Probe()
    root.add(probe)
    app = Application(root=root)
    assert len(runs) == 1

    root.remove(probe)
    root.add(probe)
    assert len(runs) == 2
    probe.width = 3
    flush_effects()
    assert runs[-1] == 3
    assert app.focused is None


def test_mounting_twice_does_nothing_the_second_time():
    log: list[str] = []
    root = LifecycleWidget(log, "root")
    Application(root=root)
    root._mount()
    assert log == ["mount root"]


# -- modal and overlay -----------------------------------------------------


def modal_app(**kwargs):
    """A root with two background widgets and a dialog ready to be opened."""
    root = RecordingWidget(width=40, height=10)
    behind = root.add(RecordingWidget(x=0, y=0, width=40, height=10))
    behind.can_focus = True
    app = Application(root=root, **kwargs)
    dialog = RecordingWidget(x=10, y=3, width=20, height=4)
    dialog.modal = True
    return app, root, behind, dialog


def test_a_modal_takes_the_input_when_it_is_mounted():
    app, root, behind, dialog = modal_app()
    assert app.modal is None
    app.overlay(dialog)
    assert app.modal is dialog
    root.remove(dialog)
    assert app.modal is None


def test_an_overlay_goes_on_top_of_everything():
    app, root, behind, dialog = modal_app()
    app.overlay(dialog)
    # Rendering walks children forwards and hit-testing backwards, so last is
    # painted over the rest and asked about a click first.
    assert root.children[-1] is dialog


def test_keys_do_not_reach_what_is_behind_a_modal():
    app, root, behind, dialog = modal_app()
    behind.focus()
    field = dialog.add(RecordingWidget())
    field.can_focus = True
    app.overlay(dialog)

    awaited(app._handle(KeyEvent("a")))
    assert field.keys == ["a"]
    assert behind.keys == []
    assert root.keys == []


def test_an_unhandled_key_does_not_bubble_out_of_a_modal():
    app, root, behind, dialog = modal_app()
    field = dialog.add(RecordingWidget())
    field.can_focus = True
    field.handles = False
    app.overlay(dialog)

    awaited(app._handle(KeyEvent("a")))
    assert (field.keys, dialog.keys) == (["a"], ["a"])
    assert root.keys == []


def test_a_modal_with_nothing_focusable_absorbs_the_keys_itself():
    app, root, behind, dialog = modal_app()
    behind.focus()
    app.overlay(dialog)
    assert app.focused is None

    awaited(app._handle(KeyEvent("a")))
    assert dialog.keys == ["a"]
    assert behind.keys == []


def test_a_click_outside_a_modal_reaches_nothing():
    app, root, behind, dialog = modal_app()
    app.overlay(dialog)
    awaited(app._handle(MouseEvent(2, 8, "left")))
    assert behind.mice == []
    assert root.mice == []
    assert dialog.mice == []


def test_a_click_inside_a_modal_arrives_in_its_own_coordinates():
    app, root, behind, dialog = modal_app()
    app.overlay(dialog)
    # The dialog sits at 10, 3; screen 12, 4 is its own 2, 1.
    awaited(app._handle(MouseEvent(12, 4, "left")))
    assert dialog.mice == [(2, 1)]
    assert behind.mice == []


def test_a_click_reaches_a_modal_nested_below_the_root():
    app, root, behind, dialog = modal_app()
    box = root.add(RecordingWidget(x=4, y=2, width=30, height=8))
    box.add(dialog)
    assert dialog.is_mounted and app.modal is dialog
    # box at 4,2 and the dialog at 10,3 within it: screen 15, 6 is its 1, 1.
    awaited(app._handle(MouseEvent(15, 6, "left")))
    assert dialog.mice == [(1, 1)]


def test_focus_cannot_be_moved_outside_an_active_modal():
    app, root, behind, dialog = modal_app()
    field = dialog.add(RecordingWidget())
    field.can_focus = True
    app.overlay(dialog)
    assert app.focused is field
    assert behind.focus() is False
    assert app.focused is field


def test_tab_stays_inside_the_modal_and_wraps():
    app, root, behind, dialog = modal_app()
    first = dialog.add(RecordingWidget())
    second = dialog.add(RecordingWidget())
    first.can_focus = second.can_focus = True
    app.overlay(dialog)

    assert app.focused is first
    assert app.focus_next() is second
    assert app.focus_next() is first


def test_opening_a_modal_focuses_its_first_field_and_closing_gives_it_back():
    app, root, behind, dialog = modal_app()
    field = dialog.add(RecordingWidget())
    field.can_focus = True
    behind.focus()
    assert app.focused is behind

    app.overlay(dialog)
    assert app.focused is field
    root.remove(dialog)
    assert app.focused is behind


def test_a_mount_handler_may_choose_the_field_itself():
    app, root, behind, dialog = modal_app()
    first = dialog.add(RecordingWidget())
    second = dialog.add(RecordingWidget())
    first.can_focus = second.can_focus = True
    dialog.mounted = lambda: second.focus()

    app.overlay(dialog)
    assert app.focused is second


def test_modals_nest_and_unwind_in_order():
    app, root, behind, dialog = modal_app()
    inner = RecordingWidget(x=1, y=1, width=5, height=2)
    inner.modal = True
    outer_field = dialog.add(RecordingWidget())
    inner_field = inner.add(RecordingWidget())
    outer_field.can_focus = inner_field.can_focus = True
    behind.focus()

    app.overlay(dialog)
    assert (app.modal, app.focused) == (dialog, outer_field)
    dialog.add(inner)
    assert (app.modal, app.focused) == (inner, inner_field)

    dialog.remove(inner)
    assert (app.modal, app.focused) == (dialog, outer_field)
    root.remove(dialog)
    assert (app.modal, app.focused) == (None, behind)


def test_a_modal_carried_off_by_an_ancestor_releases_the_input():
    app, root, behind, dialog = modal_app()
    box = root.add(RecordingWidget(width=30, height=8))
    box.add(dialog)
    assert app.modal is dialog
    root.remove(box)
    assert app.modal is None
    assert dialog.is_mounted is False


def test_overlay_refuses_when_there_is_no_root():
    app = Application()
    with pytest.raises(RuntimeError, match="no root"):
        app.overlay(Widget())


# -- every handler is async ------------------------------------------------


def test_a_synchronous_handler_is_refused_when_the_class_is_created():
    # The common mistake, caught once at import rather than at the first
    # keystroke that happens to reach it.  The message has to name both the
    # class and the method, because a traceback here points at the class
    # statement and nothing else.
    with pytest.raises(TypeError, match=r"Slow\.on_key must be `async def`"):

        class Slow(Widget):
            def on_key(self, event):
                return False


def test_a_synchronous_handler_assigned_onto_an_instance_is_refused():
    # What class creation cannot see: markup compiles to an assignment, so
    # this is the only place a generated handler's shape is checked.
    root = Widget()
    button = root.add(Widget())
    button.on_click = lambda event: True

    with pytest.raises(TypeError, match=r"Widget\.on_click must be `async def`"):
        awaited(button.emit(ClickEvent("ok")))


def test_a_lifecycle_callback_is_not_spelled_on_star():
    # It runs from add(), which runs from __init__ when a widget is
    # constructed with a parent -- and a constructor cannot await.  So it is
    # `mounted()`, outside the rule rather than an exception to it.
    seen = []

    class Probe(Widget):
        def mounted(self) -> None:
            seen.append("mounted")

    root = Widget()
    root.add(Probe())
    Application(root=root)
    assert seen == ["mounted"]


def test_a_widget_may_still_define_an_ordinary_method_called_on_something():
    # The check looks at on_* names only, and only at callables the class
    # body defines -- a plain attribute of that name is not a handler.
    class Odd(Widget):
        on_purpose = "not a handler"

    assert Odd().on_purpose == "not a handler"


# -- dispatching a refinement of a mouse action ----------------------------
#
# `dispatch_mouse' looks the handler up under `event.handler', the way `emit'
# does, which is what makes a DoubleClickEvent reach `on_double_click' and
# nothing else.  A plain MouseEvent derives `on_mouse', so that path is the
# one it always was.


class Clickable(Widget):
    """Records mouse actions, keeping the two gestures apart."""

    def __init__(self, name: str, doubles: bool = False, claims: bool = True, **kw):
        super().__init__(**kw)
        self.name = name
        self.claims = claims
        self.presses: list[str] = []
        self.doubles: list[str] = []
        self._wants_doubles = doubles
        if doubles:
            self.on_double_click = self._on_double_click  # type: ignore[method-assign]

    async def on_mouse(self, event: MouseEvent) -> bool:
        self.presses.append(self.name)
        return self.claims

    async def _on_double_click(self, event: MouseEvent) -> bool:
        self.doubles.append(self.name)
        return self.claims


def test_a_double_click_reaches_on_double_click_and_not_on_mouse():
    root = Clickable("root", doubles=True, width=40, height=10)
    awaited(root.dispatch_mouse(DoubleClickEvent(1, 1, "left", "press")))

    assert root.doubles == ["root"]
    assert root.presses == []


def test_a_plain_press_is_unaffected_by_the_handler_lookup():
    root = Clickable("root", doubles=True, width=40, height=10)
    awaited(root.dispatch_mouse(MouseEvent(1, 1, "left", "press")))

    assert root.presses == ["root"]
    assert root.doubles == []


def test_a_widget_with_no_double_click_handler_lets_it_fall_outward():
    """Skipped is what "did not claim it" already means here, so the event
    reaches an ancestor exactly as an unhandled press does -- which is why no
    widget needs a stub."""
    root = Clickable("root", doubles=True, width=40, height=10)
    inner = root.add(Clickable("inner", x=2, y=2, width=10, height=4))

    awaited(root.dispatch_mouse(DoubleClickEvent(3, 3, "left", "press")))

    assert inner.doubles == []
    assert inner.presses == []
    assert root.doubles == ["root"]


def test_the_innermost_double_click_handler_wins():
    root = Clickable("root", doubles=True, width=40, height=10)
    inner = root.add(Clickable("inner", doubles=True, x=2, y=2, width=10, height=4))

    awaited(root.dispatch_mouse(DoubleClickEvent(3, 3, "left", "press")))

    assert inner.doubles == ["inner"]
    assert root.doubles == []


def test_a_double_click_arrives_in_the_widgets_own_coordinates():
    root = Clickable("root", width=40, height=10)
    inner = root.add(Clickable("inner", doubles=True, x=4, y=2, width=10, height=4))
    seen: list[tuple[int, int]] = []

    async def record(event):
        seen.append((event.x, event.y))
        return True

    inner.on_double_click = record
    awaited(root.dispatch_mouse(DoubleClickEvent(6, 3, "left", "press")))

    assert seen == [(2, 1)]


def test_a_double_click_outside_a_modal_reaches_nothing(terminal):
    """Inherited from `translated' keeping the subclass, so `_dispatch_mouse'
    reroutes one without knowing the class exists."""
    root = Clickable("root", doubles=True, width=40, height=10)
    app = Application(root, terminal=terminal)
    dialog = Clickable("dialog", doubles=True, x=10, y=4, width=8, height=3)
    dialog.modal = True
    app.root.add(dialog)

    awaited(app._handle(DoubleClickEvent(1, 1, "left", "press")))
    assert (dialog.doubles, root.doubles) == ([], [])

    awaited(app._handle(DoubleClickEvent(11, 5, "left", "press")))
    assert dialog.doubles == ["dialog"]
