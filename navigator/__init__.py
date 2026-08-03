"""Assets belonging to the Navigator application.

Not code -- ``nav.py`` at the repository root is still the application.  This
package exists so the things it loads at run time have a name the project owns
and so they travel with an installed copy: a top-level ``data/`` directory
reaches neither a wheel nor ``site-packages`` without claiming a name no
project should.
"""
