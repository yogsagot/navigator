"""The dialog widgets: the Colors dialog's *Dialogs* group, one component each.

A **group**, not a component -- see *Components come in groups* in
``navml/DESIGN.md``.  Every control a dialog is made of lives in here beside
``Modal`` and ``Dialog`` themselves, and this file imports none of them, so
that importing one does not drag in the rest.  Reach a component through
``navml.widgets`` or through its own directory::

    from navml.widgets import Button
    from navml.widgets.dialog.button import Button
"""
