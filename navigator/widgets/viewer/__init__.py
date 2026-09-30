"""The internal viewer (F3): `FileViewer` inside `FileWindow`, the quick view
(Ctrl+Q), and the viewer's Find, Go to and *Search Progress* boxes.

A **group**, not a component -- see *Components come in groups* in
``navml/DESIGN.md``.  This file imports none of its members, so that importing
one does not drag in the rest.  Reach a member through ``navigator.widgets``
or through its own directory::

    from navigator.widgets import FileViewer
    from navigator.widgets.viewer.file_viewer import FileViewer
"""
