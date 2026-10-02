"""Navigator's models: tables in the one database, declared in markup.

A library the way :mod:`navml.models` is one -- every directory is a component
whose root extends :class:`navkit.database.Model` -- registered with the
component finder here, and importing none of them.  :mod:`.file_record` is the
plain-Python base the per-file histories share.
"""

import navml

navml.register(__name__)
