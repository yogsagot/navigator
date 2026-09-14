"""A blank, stylable gap -- a component written in Python alone.

There is no ``spacer.nml`` and no ``spacer_nml.py``, so :mod:`navml._merge`
claims nothing here and the stock :class:`importlib.machinery.SourceFileLoader`
imports this module.  That is the point of it: an ordinary
:class:`navkit.Widget` subclass already *is* a component, with no base class of
navml's, no decorator and no registration.  Adding a ``spacer.nml`` later would
not change one line of this file.
"""

from __future__ import annotations

from navkit.screen import Surface
from navkit.widget import Widget


class Spacer(Widget):
    """Fills its area with its resolved background and nothing else."""

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
