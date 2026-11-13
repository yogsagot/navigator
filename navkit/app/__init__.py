"""The parts of :class:`navkit.application.Application`, one module a feature.

Each is a :class:`navkit.widget.Mixin` the class lists ahead of its own body:
``focus`` (modal, capture, focus), ``painting`` (the frame and lending the
terminal), ``dispatch`` (the loop and the mouse) and ``input`` (keys, commands
and the terminal's input).  They import what they share from
:mod:`navkit.application`, which imports them just before its class -- so the
application module is always the one imported first, here too.
"""

import navkit.application  # noqa: F401  -- first, whichever of these is asked for
