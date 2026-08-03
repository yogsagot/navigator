"""Navigator -- a recreation of DOS Navigator for POSIX terminals.

The application is :mod:`navigator.__main__`, run with ``python -m navigator``
or through the ``nav`` console script.  Its run-time assets live beside it in
:mod:`navigator.styles`, so they travel with an installed copy: anything
outside a package reaches neither a wheel nor site-packages.

This module stays empty deliberately.  Importing the package should not read a
stylesheet or build a widget tree, so all of that happens in ``__main__`` and
nothing here runs as a side effect of ``import navigator``.
"""
