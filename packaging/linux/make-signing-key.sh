#!/bin/sh
# Create the key that signs the apt and dnf repositories.  Run this once.
#
#   packaging/linux/make-signing-key.sh [OUTPUT_DIR]
#
# gpg prompts for the passphrase itself, so it is never typed on a command
# line, never lands in shell history and never reaches a log.
#
# Two decisions worth knowing about:
#
# RSA-4096 rather than Ed25519.  Ed25519 is the better modern choice and is
# accepted by apt and by rpm >= 4.16, which covers every distro this project
# targets.  RSA is chosen anyway because the asymmetry is brutal: users import
# this key *once* and keep it, so if some client rejects it the fix is
# reissuing a key everybody has already trusted.  A larger signature is the
# cheaper side of that trade.
#
# A separate signing subkey.  The primary key certifies and never leaves this
# machine; only the subkey is exported for CI.  If the CI secret leaks, the
# subkey is revoked and replaced without users having to trust a new key --
# which is the whole point of the split, and is impossible after the fact.
set -eu

OUT=${1:-$HOME/navigator-fm-signing}
NAME=${NAME:-Navigator FM package signing}
EMAIL=${EMAIL:-juris.krumgolds@gmail.com}
UID_STR="$NAME <$EMAIL>"

command -v gpg > /dev/null || { echo "make-signing-key.sh: gpg is not installed" >&2; exit 1; }

if gpg --list-keys "$UID_STR" > /dev/null 2>&1; then
    echo "make-signing-key.sh: a key for '$UID_STR' already exists." >&2
    echo "  Delete it first, or set NAME= to something else." >&2
    echo "  Existing:" >&2
    gpg --list-keys --keyid-format long "$UID_STR" >&2
    exit 1
fi

mkdir -p "$OUT"
chmod 700 "$OUT"

echo "Creating the certifying primary key.  gpg will ask for a passphrase --"
echo "choose a strong one and keep it.  It protects the primary, which stays"
echo "on this machine; CI's copy is stripped of it further down."
echo
gpg --quick-generate-key "$UID_STR" rsa4096 cert 5y

FPR=$(gpg --list-keys --with-colons "$UID_STR" | awk -F: '/^fpr:/ { print $10; exit }')
[ -n "$FPR" ] || { echo "make-signing-key.sh: could not read the fingerprint back" >&2; exit 1; }

echo
echo "Adding the signing subkey (this is the one CI gets)."
gpg --quick-add-key "$FPR" rsa4096 sign 2y

# The public half, in both encodings.  apt wants the dearmoured form in
# /usr/share/keyrings; rpm --import wants the armoured one.  Publishing both
# costs nothing and saves every user a conversion step.
gpg --armor --export "$FPR" > "$OUT/navigator-fm-archive-keyring.asc"
gpg --export "$FPR" > "$OUT/navigator-fm-archive-keyring.gpg"

# The secret half, subkeys only: the exported block carries a stub in place of
# the primary key, so this file cannot certify anything or make a new subkey.
#
# It is exported *unprotected*, and that is a considered choice rather than a
# shortcut.  nfpm cannot decrypt a subkey whose primary is the `gnu-dummy'
# stub this export leaves behind: given a protected subkeys-only file it fails
# every time with `signing key is encrypted', whatever the passphrase.  The
# alternatives were to hand CI the full secret key -- which would put the
# certifying primary on a build runner and defeat the whole arrangement -- or
# to stop letting nfpm sign at all.  Dropping the passphrase costs least,
# because it was never protecting anything: it would have lived in the same
# GitHub secret store as the key, so an attacker reading one reads both.  What
# actually keeps the primary safe is that it is not in this file.
umask 077
STRIP=$(mktemp -d)
trap 'rm -rf "$STRIP"' EXIT INT TERM
chmod 700 "$STRIP"
gpg --armor --export-secret-subkeys "$FPR" > "$STRIP/protected.asc"
gpg --homedir "$STRIP" --batch --quiet --import "$STRIP/protected.asc"

echo
echo "Removing the passphrase from CI's copy -- gpg will ask for it once more,"
echo "then for the new one: leave the new one EMPTY and confirm."
gpg --homedir "$STRIP" --edit-key "$FPR" passwd save

gpg --homedir "$STRIP" --batch --armor --export-secret-subkeys "$FPR" \
    > "$OUT/ci-signing-subkey.asc"

# An export that still carries `protect count' would be one nfpm cannot use,
# and the failure would only show up in CI, so it is caught here instead.
if gpg --list-packets "$OUT/ci-signing-subkey.asc" 2>/dev/null | grep -q "protect count"; then
    echo "make-signing-key.sh: the exported subkey is still passphrase-protected." >&2
    echo "          nfpm cannot sign with it.  Re-run and leave the new" >&2
    echo "          passphrase empty when gpg asks." >&2
    exit 1
fi
if ! gpg --list-packets "$OUT/ci-signing-subkey.asc" 2>/dev/null | grep -q "skey\["; then
    echo "make-signing-key.sh: the export carries no secret key material." >&2
    exit 1
fi

# nfpm parses key_id as a 64-bit integer, so it takes the 16-hex-digit long
# key id and rejects a 40-character fingerprint outright.
#
# It must be the *signing subkey's* id, not the primary's.  The export above
# is --export-secret-subkeys, so what CI holds is a stub primary with no
# private key behind it -- and the primary is certify-only in any case.  Given
# the primary's id nfpm searches for a signing key, finds the stub, and fails
# with `no valid signing keys`, which names neither the key nor the reason.
# Given the subkey's it signs.  gpg takes a subkey id for --local-user
# happily, so the repository scripts are unaffected by the choice.
LONG=$(gpg --list-keys --with-colons "$UID_STR" | awk -F: '/^sub:/ && $12 ~ /s/ { print $5; exit }')

echo
echo "================================================================"
echo "Key created."
echo "  primary fingerprint: $FPR"
echo "  signing subkey id:   $LONG"
echo
echo "Commit the public halves -- they are public by definition, and the"
echo "release workflow copies them from there into the published site:"
echo "  cp $OUT/navigator-fm-archive-keyring.asc packaging/linux/repo/"
echo "  cp $OUT/navigator-fm-archive-keyring.gpg packaging/linux/repo/"
echo
echo "Add these to GitHub -> Settings -> Secrets and variables -> Actions:"
echo "  GPG_PRIVATE_KEY   the contents of $OUT/ci-signing-subkey.asc"
echo "  (GPG_PASSPHRASE is no longer needed -- CI's copy has no passphrase)"
echo "  GPG_KEY_ID        $LONG        (a repository *variable*, not a secret --"
echo "                                     key ids are public.  This is the"
echo "                                     *signing subkey's* long id, which is"
echo "                                     what nfpm can actually sign with; the"
echo "                                     primary's id yields 'no valid signing"
echo "                                     keys', and a full fingerprint is"
echo "                                     rejected as a number out of range.)"
echo
echo "Then delete the exported secret, which has served its purpose:"
echo "  shred -u $OUT/ci-signing-subkey.asc"
echo
echo "Back up the primary key somewhere offline before you do anything else:"
echo "  gpg --armor --export-secret-keys $FPR"
echo "Losing it means never being able to issue a new subkey under this"
echo "identity, and every user having to trust a replacement key by hand."
echo "================================================================"
