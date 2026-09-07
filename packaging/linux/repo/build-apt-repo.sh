#!/bin/sh
# Add a .deb to the apt repository and regenerate its signed index.
#
#   packaging/linux/repo/build-apt-repo.sh SITE_DIR DEB [DEB...]
#
# SITE_DIR is the *existing* published site, checked out from the gh-pages
# branch.  This script adds to it; it never builds one from scratch.  That
# distinction is the whole reason the branch is checked out first: apt builds
# its index by scanning the pool, so a run over a pool holding only today's
# package publishes an index that has forgotten every previous release.
# Everyone who pinned a version, or who wants to roll back, then gets a 404.
# The count assertion at the end is what keeps that from regressing quietly.
#
# Signing: apt verifies the *index*, not the packages -- per-package integrity
# comes from the SHA256 recorded in Packages.  So the signature that matters
# here is the one over Release, in both of its spellings: InRelease for modern
# clients, Release.gpg for older ones.
#
# Environment:
#   GPG_KEY_ID      fingerprint of the signing key (required)
#   GPG_PASSPHRASE  optional; if unset, gpg's agent is left to ask
set -eu

SITE=${1:?usage: build-apt-repo.sh SITE_DIR DEB [DEB...]}
shift
[ $# -gt 0 ] || { echo "build-apt-repo.sh: no .deb given" >&2; exit 1; }

: "${GPG_KEY_ID:?build-apt-repo.sh: GPG_KEY_ID is not set}"
command -v apt-ftparchive > /dev/null \
    || { echo "build-apt-repo.sh: apt-ftparchive is missing (apt-utils)" >&2; exit 1; }

CONF=$(cd "$(dirname "$0")" && pwd)/apt-release.conf
DEB=$SITE/deb
POOL=$DEB/pool/main/n/navigator-fm

# Architectures the index is published under.  The package is `all', which is
# the correct and sufficient answer, but a copy of the index under each real
# architecture costs two kilobytes and removes a whole class of "no
# installation candidate" reports from clients that handle `all'-only
# repositories badly.
ARCHES="amd64 arm64"

mkdir -p "$POOL" "$DEB/dists/stable/main/binary-all"
for arch in $ARCHES; do mkdir -p "$DEB/dists/stable/main/binary-$arch"; done

INDEX=$DEB/dists/stable/main/binary-all/Packages
before=0
[ -f "$INDEX" ] && before=$(grep -c '^Package:' "$INDEX" || true)

for deb in "$@"; do
    [ -f "$deb" ] || { echo "build-apt-repo.sh: no such file: $deb" >&2; exit 1; }
    echo "build-apt-repo.sh: + $(basename "$deb")"
    cp "$deb" "$POOL/"
done

# Paths inside Packages are recorded relative to the working directory, so the
# scan has to run from the root the web server will serve.
cd "$DEB"

apt-ftparchive --arch all packages pool > dists/stable/main/binary-all/Packages
gzip -9nkf dists/stable/main/binary-all/Packages
for arch in $ARCHES; do
    cp dists/stable/main/binary-all/Packages    "dists/stable/main/binary-$arch/Packages"
    cp dists/stable/main/binary-all/Packages.gz "dists/stable/main/binary-$arch/Packages.gz"
done

# Release is a digest of everything beside it, so the previous one and its
# signatures have to be out of the way before the new one is computed --
# otherwise it hashes its own predecessor and the result is self-referential.
rm -f dists/stable/Release dists/stable/Release.gpg dists/stable/InRelease
apt-ftparchive -c "$CONF" release dists/stable > dists/stable/Release.tmp
mv dists/stable/Release.tmp dists/stable/Release

sign() {
    if [ -n "${GPG_PASSPHRASE:-}" ]; then
        printf '%s' "$GPG_PASSPHRASE" | gpg --batch --yes --pinentry-mode loopback \
            --passphrase-fd 0 --local-user "$GPG_KEY_ID" "$@"
    else
        gpg --batch --yes --local-user "$GPG_KEY_ID" "$@"
    fi
}

sign --clearsign     -o dists/stable/InRelease   dists/stable/Release
sign --detach-sign --armor -o dists/stable/Release.gpg dists/stable/Release

after=$(grep -c '^Package:' dists/stable/main/binary-all/Packages)

# The guard has to measure against what is *published*, not against what this
# directory happened to contain.  Comparing before with after only catches a
# loss inside one run, which cannot happen -- the run only ever adds.  The
# failure worth catching is the opposite: SITE_DIR was never populated from
# gh-pages, so `before' is 0, `after' is 1, and a one-package index quietly
# replaces a repository with a dozen releases in it.  EXPECT_AT_LEAST is how
# the caller passes in the live count; the workflow reads it off the site.
expect=${EXPECT_AT_LEAST:-$before}
if [ "$after" -lt "$expect" ]; then
    echo "build-apt-repo.sh: the index would publish $after package(s) where" >&2
    echo "  at least $expect are already live -- $((expect - after)) would vanish." >&2
    echo "  SITE_DIR was probably not checked out from gh-pages before this ran." >&2
    exit 1
fi

echo "build-apt-repo.sh: $after package(s) indexed, signed by $GPG_KEY_ID"
