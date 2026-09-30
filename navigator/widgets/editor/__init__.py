"""The internal editor (F4): `FileEditor` inside `EditWindow`.

A **group**, not a component -- see *Components come in groups* in
``navml/DESIGN.md``.  This file imports none of its members, so that importing
one does not drag in the rest.  Reach a member through ``navigator.widgets``
or through its own directory::

    from navigator.widgets import EditWindow
    from navigator.widgets.editor.edit_window import EditWindow
"""
