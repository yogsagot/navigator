#!/bin/sh
# Remove what postinstall generated.  The .pyc files are not in the package
# manifest, so neither dpkg nor rpm knows to take them away, and the directory
# would be left behind holding nothing but caches.
#
# The guard matters: this same script runs on *upgrade* as well as removal --
# dpkg passes `upgrade', rpm passes the number of copies that will remain (1).
# Clearing the cache mid-upgrade would merely be wasteful; removing the
# directory would break the upgraded package.
set -e
case "${1:-0}" in
    remove|purge|0)
        find /usr/lib/navigator-fm -name '__pycache__' -type d -prune \
            -exec rm -rf {} + 2>/dev/null || :
        rmdir /usr/lib/navigator-fm 2>/dev/null || :
        ;;
esac
