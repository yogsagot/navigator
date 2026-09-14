"""The widget library.

Every module in here is a component, in one of the three shapes
:mod:`navml._merge` describes.  The re-exports below are the ordinary way in --
``from navml.widgets import Button`` -- and they also mean the shape a
component happens to be written in never reaches the call site.
"""

import navml

navml.register(__name__)

from navml.widgets.button import Button  # noqa: E402  (after register)
from navml.widgets.framed_button import FramedButton  # noqa: E402
from navml.widgets.label import Label  # noqa: E402
from navml.widgets.spacer import Spacer  # noqa: E402

__all__ = ["Button", "FramedButton", "Label", "Spacer"]
