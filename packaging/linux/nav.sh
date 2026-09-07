#!/bin/sh
# Navigator's launcher, as installed by the .deb and .rpm.
#
# The application and its dependencies live in a private directory rather than
# in the system site-packages, so a system package neither collides with a pip
# install nor is broken by one.  Everything in that directory is pure Python,
# which is what lets one architecture-independent package serve every
# interpreter from 3.12 onwards -- a venv could not, having its minor version
# baked into `lib/python3.N/site-packages` and into pyvenv.cfg.
#
# The two interpreter flags are load-bearing, not hygiene:
#
#   -P  keeps the current directory off sys.path.  A file manager is launched
#       inside arbitrary directories, and without this a directory that merely
#       *contains* an icons.py or a pyte.py shadows the real module -- so
#       Navigator would die on startup in that one directory and nowhere else.
#   -s  drops the user's ~/.local site-packages, so a half-broken pip
#       environment cannot take the system package down with it.
#
# Not -E: that would clear PYTHONPATH, which is how we find ourselves.
NAV_LIB=/usr/lib/navigator-fm
PYTHONPATH="$NAV_LIB${PYTHONPATH:+:$PYTHONPATH}" \
    exec /usr/bin/python3 -sP -m navigator "$@"
