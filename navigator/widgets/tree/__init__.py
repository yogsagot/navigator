"""The directory trees: `DirectoryTree` in the passive panel's place (Ctrl+T),
the *Choose Directory* dialog (Alt+T) and the *Directory Tree* window.

A **group**, not a component -- see *Components come in groups* in
``navml/DESIGN.md``.  This file imports none of its members, so that importing
one does not drag in the rest.  Reach a member through ``navigator.widgets``
or through its own directory::

    from navigator.widgets import ChangeDirDialog
    from navigator.widgets.tree.change_dir_dialog import ChangeDirDialog
"""
