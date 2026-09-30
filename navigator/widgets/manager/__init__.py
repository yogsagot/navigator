"""The file manager window: `Manager`, the two `Panel`s it holds, and the
*Select group* dialog the panels ask their masks with.

A **group**, not a component -- see *Components come in groups* in
``navml/DESIGN.md``.  This file imports none of its members, so that importing
one does not drag in the rest.  Reach a member through ``navigator.widgets``
or through its own directory::

    from navigator.widgets import Manager
    from navigator.widgets.manager.manager import Manager
"""
