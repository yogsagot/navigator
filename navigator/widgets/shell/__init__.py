"""The screen around the windows: the root `Shell`, the console behind the
desktop, the menu bar's `MainMenu` and `Clock`, the key bar, and the command
line with its completion drop-down.

A **group**, not a component -- see *Components come in groups* in
``navml/DESIGN.md``.  This file imports none of its members, so that importing
one does not drag in the rest.  Reach a member through ``navigator.widgets``
or through its own directory::

    from navigator.widgets import Clock
    from navigator.widgets.shell.clock import Clock
"""
