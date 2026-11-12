"""``Window.local_menu``: a window's own menu, opened by a right click or Shift+F10.

A window naming one of its menus (``local_menu: volumes_menu``) answers a right
click and the Menu key with that menu -- the same list it puts on the bar --
where a window had to build the same entries again in Python.  One naming none
answers neither: Shift+F10 is greyed there and a right click goes on outward.
"""

from __future__ import annotations

from conftest import run_app

from navkit.application import Application
from navkit.commands import Command
from navkit.events import ContextMenuEvent
from navkit.widget import Widget

from navml.checks import check
from navml.generator import generate
from navml.parser import parse
from navml.resolve import resolve
from navml.widgets.menu.commands import ShowContextMenu
from navml.widgets.menu.popup_menu.popup_menu import PopupMenu


class Rescan(Command):
    title = "Rescan"


DOCUMENT = (
    "from navml.widgets.window import Window\n"
    "from navml.widgets.menu.sub_menu import SubMenu\n"
    "from navml.widgets.menu.menu_item import MenuItem\n"
    f"from {__name__} import Rescan\n\n"
    "Widget_(Window):\n"
    "    {line}\n"
    "    SubMenu: text='~T~hings'\n"
    "        id: things_menu\n"
    "        MenuItem: text='~R~e-read', command=Rescan\n"
)


def window_class(line: str):
    resolved = resolve(parse(DOCUMENT.replace("{line}", line), filename="widget.nml"))
    check(resolved)
    namespace: dict = {"__name__": "generated"}
    exec(compile(generate(resolved), "widget_nml.py", "exec"), namespace)
    return namespace["Widget_"]


def test_a_window_naming_its_menu_offers_it():
    window = window_class("local_menu: things_menu")()
    assert window.context_menu() is window.things_menu
    assert window.enables(ShowContextMenu()) is True


def test_a_window_naming_none_offers_nothing_and_shift_f10_is_greyed():
    window = window_class("title: 'plain'")()
    assert window.context_menu() is None
    assert window.enables(ShowContextMenu()) is False


def test_a_right_click_opens_the_menu_and_one_without_goes_on_outward():
    seen = []
    for line, expect in (("local_menu: things_menu", True), ("title: 'plain'", False)):
        root = Widget(width=80, height=25)
        window = window_class(line)(x=2, y=2, width=30, height=10)
        root.add(window)
        app = Application(root)
        answered = []

        async def right_click(w=window):
            answered.append(await w.on_context_menu(ContextMenuEvent(x=3, y=3, button="right")))

        run_app(app, [lambda a: a.spawn(right_click()), lambda a: None,
                      lambda a: seen.append(isinstance(a.modal, PopupMenu))])
        assert answered == [expect]
        assert seen[-1] is expect
