"""The file operations over a panel's selection: Copy and Rename/move (F5/F6)
with their progress box and overwrite query, Create symlink (Shift+F5), Make
directory (F7), erase (F8/Del) with its progress box and query, and File
Attributes (Alt+E).

A **group**, not a component -- see *Components come in groups* in
``navml/DESIGN.md``.  This file imports none of its members, so that importing
one does not drag in the rest.  Reach a member through ``navigator.widgets``
or through its own directory::

    from navigator.widgets import CopyDialog
    from navigator.widgets.file_ops.copy_dialog import CopyDialog
"""
