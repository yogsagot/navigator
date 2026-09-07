#!/bin/sh
# Byte-compile the vendored tree.
#
# /usr/lib/navigator-fm is root-owned, so an ordinary user's runs can never
# write a __pycache__ of their own: without this, *every* launch by *every*
# user pays the full compile cost of the import graph rather than the first
# one paying it once.  This is what dh_python3 does for a distro Python
# package, and the reason is the same.
set -e
/usr/bin/python3 -m compileall -q /usr/lib/navigator-fm >/dev/null 2>&1 || :
