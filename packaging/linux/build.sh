#!/bin/sh
# Build the .deb and the .rpm.
#
#   packaging/linux/build.sh [OUTPUT_DIR]
#
# Needs a wheel in dist/ (run `python -m build` first) and nfpm on PATH or in
# NFPM.  Everything it writes lives under build/, which is gitignored.
#
# The staging tree is assembled by pip rather than by copying directories, so
# the files that reach the package are exactly the ones the wheel declares --
# navigator/styles/*.nss included.  Those are found through
# importlib.resources, and a package that drops them yields an application
# that starts and then fails to theme, so the assertions below check for them
# by name rather than trusting the copy.
set -eu

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"

OUT=${1:-build/pkg}
LIB=build/root/usr/lib/navigator-fm
NFPM=${NFPM:-nfpm}
PYTHON=${PYTHON:-python3}

WHEEL=$(ls dist/navigator_fm-*-py3-none-any.whl 2>/dev/null | head -1)
[ -n "$WHEEL" ] || { echo "build.sh: no wheel in dist/ -- run: $PYTHON -m build" >&2; exit 1; }

# The version the wheel actually carries, not one typed here twice.
PEP440=$(echo "$WHEEL" | sed 's|.*/navigator_fm-||; s|-py3-none-any.whl||')
NAV_VERSION=$("$PYTHON" packaging/linux/native_version.py "$PEP440")
NAV_RELEASE=${NAV_RELEASE:-1}
export NAV_VERSION NAV_RELEASE

echo "build.sh: $WHEEL"
echo "build.sh: $PEP440 -> $NAV_VERSION-$NAV_RELEASE"

rm -rf build/root "$OUT"
mkdir -p "$LIB" build/root/usr/bin "$OUT"

# --no-compile because a .pyc is tagged with the interpreter that wrote it and
# is useless -- worse, confusing -- on any other.  The postinstall generates
# them on the target instead, where they match.
"$PYTHON" -m pip install --quiet --no-compile --target "$LIB" "$WHEEL"

# pip --target leaves the console-script shims behind; the shim we ship is
# ours, and theirs carry a shebang pointing at whatever built the package.
rm -rf "$LIB/bin"
find build/root -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find build/root -name '*.pyc' -delete

install -m 0755 packaging/linux/nav.sh build/root/usr/bin/nav

# --- the assertions, in the order they would actually fail ----------------
[ -f "$LIB/navigator/__main__.py" ] || { echo "build.sh: no application in the tree" >&2; exit 1; }
[ -f "$LIB/navigator/styles/navigator.nss" ] || { echo "build.sh: the stylesheet is missing" >&2; exit 1; }

themes=$(ls "$LIB"/navigator/styles/themes/*.nss 2>/dev/null | wc -l)
[ "$themes" -eq 11 ] || { echo "build.sh: expected 11 themes, packaged $themes" >&2; exit 1; }

# One noarch package is only honest while every dependency is pure Python.
if find "$LIB" -name '*.so' | grep -q .; then
    echo "build.sh: a compiled extension is in the tree -- 'arch: all' is now a lie," >&2
    echo "          and the package needs to be built per distro.  See nfpm.yaml." >&2
    exit 1
fi

"$PYTHON" -c "import sys; sys.path.insert(0, '$LIB'); import navigator, navkit, pyte" \
    || { echo "build.sh: the staged tree does not import" >&2; exit 1; }

echo "build.sh: staged $(du -sh "$LIB" | cut -f1) in $LIB"

# --- the packages ----------------------------------------------------------
for format in deb rpm; do
    "$NFPM" package -f packaging/linux/nfpm.yaml -p "$format" -t "$OUT"
done

ls -l "$OUT"
