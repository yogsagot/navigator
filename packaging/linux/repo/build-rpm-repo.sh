#!/bin/sh
# Add an .rpm to the dnf repository and regenerate its signed metadata.
#
#   packaging/linux/repo/build-rpm-repo.sh SITE_DIR RPM [RPM...]
#
# Same rule as the apt side: SITE_DIR is the existing published site, and
# createrepo_c indexes whatever .rpm files it finds, so the previous ones have
# to be there.  `--update' reuses cached metadata for unchanged files; it does
# not excuse them from being present.
#
# RPM's signing model is the mirror image of apt's, and both halves are
# needed:
#
#   gpgcheck=1       verifies the signature *inside each .rpm*.  nfpm puts
#                    that there at build time -- not here.
#   repo_gpgcheck=1  verifies repomd.xml.asc, the detached signature over the
#                    metadata, which is what this script writes.
#
# Signing only one of the two leaves a repository that either warns on every
# install or refuses outright, depending on which half is missing.
#
# Environment:
#   GPG_KEY_ID      fingerprint of the signing key (required)
#   GPG_PASSPHRASE  optional; if unset, gpg's agent is left to ask
set -eu

SITE=${1:?usage: build-rpm-repo.sh SITE_DIR RPM [RPM...]}
shift
[ $# -gt 0 ] || { echo "build-rpm-repo.sh: no .rpm given" >&2; exit 1; }

: "${GPG_KEY_ID:?build-rpm-repo.sh: GPG_KEY_ID is not set}"
command -v createrepo_c > /dev/null \
    || { echo "build-rpm-repo.sh: createrepo_c is missing (package: createrepo-c)" >&2; exit 1; }

RPMDIR=$SITE/rpm
mkdir -p "$RPMDIR"

before=$(ls "$RPMDIR"/*.rpm 2>/dev/null | wc -l)

for rpm in "$@"; do
    [ -f "$rpm" ] || { echo "build-rpm-repo.sh: no such file: $rpm" >&2; exit 1; }
    echo "build-rpm-repo.sh: + $(basename "$rpm")"
    cp "$rpm" "$RPMDIR/"
done

cd "$RPMDIR"
createrepo_c --update --retain-old-md 0 .

rm -f repodata/repomd.xml.asc
if [ -n "${GPG_PASSPHRASE:-}" ]; then
    printf '%s' "$GPG_PASSPHRASE" | gpg --batch --yes --pinentry-mode loopback \
        --passphrase-fd 0 --local-user "$GPG_KEY_ID" \
        --detach-sign --armor -o repodata/repomd.xml.asc repodata/repomd.xml
else
    gpg --batch --yes --local-user "$GPG_KEY_ID" \
        --detach-sign --armor -o repodata/repomd.xml.asc repodata/repomd.xml
fi

after=$(ls ./*.rpm 2>/dev/null | wc -l)

# See the note in build-apt-repo.sh: comparing with `before' cannot catch the
# failure that matters, because a run that started from an empty directory has
# nothing to lose.  EXPECT_AT_LEAST carries the live count in.
expect=${EXPECT_AT_LEAST:-$before}
if [ "$after" -lt "$expect" ]; then
    echo "build-rpm-repo.sh: would publish $after package(s) where at least" >&2
    echo "  $expect are already live -- $((expect - after)) would vanish." >&2
    echo "  SITE_DIR was probably not checked out from gh-pages before this ran." >&2
    exit 1
fi

echo "build-rpm-repo.sh: $after package(s) indexed, metadata signed by $GPG_KEY_ID"
