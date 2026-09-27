"""The layout containers: widgets whose one job is placing their children.

A **group**, not a component: every layout is its own component directory in
here, beside the ``layout`` base they share, and this file imports none of
them -- importing one layout must not drag in the rest, for the reason
``navml/widgets/__init__.py`` re-exports lazily.  Reach a layout through
``navml.widgets`` or through its own directory::

    from navml.widgets import HorizontalLayout
    from navml.widgets.layout.horizontal_layout import HorizontalLayout
"""
