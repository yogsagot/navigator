"""The menu widgets: Turbo Vision's ``TMenuBar`` and ``TMenuBox``, and the
tree they are read from.

A **group**, not a component -- see *Components come in groups* in
``navml/DESIGN.md``.  The tree is written in markup, one block per entry::

    MenuBar:
        SubMenu:
            text: "~F~ile"
            MenuItem:
                text: "~M~ake directory"
                command: MakeDirectory
            MenuLine:

``SubMenu``, ``MenuItem`` and ``MenuLine`` are widgets that are never shown:
data in the tree, which the bar and the boxes it opens read and paint as
rows.  DOS Navigator's Colors dialog gives them the six *Menus* slots, [2] to
[7], and ``navml/DESIGN.md``'s *Menus* has why each part went the way it did.
"""
