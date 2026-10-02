"""The library's models: tables in the one database, declared in markup.

A **library**, the way :mod:`navml.widgets` is one: every directory in here is
a component whose root extends :class:`navkit.database.Model`, and this file
registers the package with the component finder and imports none of them.
"""

import navml

navml.register(__name__)
