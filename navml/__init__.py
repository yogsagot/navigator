"""navml -- the markup language and the widget library built on :mod:`navkit`.

A component is written as markup (``button.nml``), as Python (``button.py``),
or as both, and the three are interchangeable: the consumer writes
``from navml.widgets.button import Button`` and cannot tell which shape it is
looking at.  :mod:`navml._merge` is what makes that true; *The two halves of a
component* in ``navml/DESIGN.md`` records why it works the way it does.

Nothing here depends on the file manager, and nothing in :mod:`navkit` depends
on this.  The dependency direction is strictly one way.
"""

from navkit.reactive import bind, computed, effect, reactive
from navkit.widget import Widget

from navml._merge import ComponentError, install, register
from navml.errors import MarkupError

__all__ = [
    "ComponentError",
    "MarkupError",
    "Widget",
    "bind",
    "computed",
    "effect",
    "install",
    "reactive",
    "register",
]

# A component package registers itself, but the finder has to exist before the
# first one does -- and importing anything under `navml' runs this file first.
install()
