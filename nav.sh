#!/bin/bash
# Run Navigator from this checkout.
#   nav.sh [--install | --update | --upgrade] [nav arguments...]
#   --install  create the virtualenv (if missing) and install the requirements
#   --update   pull the latest master first
#   --upgrade  pull the latest master and reinstall the requirements
set -e

# The repository, wherever the script is called from (a symlink in ~/bin included). No cd:
# the panels open in the caller's directory and relative directory arguments stay relative to it.
repo="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

if [[ "$1" == --install ]]
then
   if [[ ! -x "$repo/venv/bin/python" ]]
   then
      python="$(command -v python3.12 || command -v python3)" || { echo "No python3 found" >&2; exit 1; }
      echo "Creating virtualenv at $repo/venv with $python"
      "$python" -m venv "$repo/venv"
   fi
   echo "Installing requirements"
   "$repo/venv/bin/pip" install -r "$repo/requirements.txt"
   shift
fi

if [[ ! -x "$repo/venv/bin/python" ]]
then
   echo "No virtualenv at $repo/venv; create it with:" >&2
   echo "   $0 --install" >&2
   exit 1
fi

case "$1" in
   --update)
      echo "Running git update"
      git -C "$repo" pull origin master
      shift
      ;;
   --upgrade)
      echo "Running pip upgrade"
      git -C "$repo" pull origin master
      "$repo/venv/bin/pip" install -r "$repo/requirements.txt"
      shift
      ;;
esac

# exec hands the terminal, signals and the exit status straight to Navigator.
exec env PYTHONPATH="$repo${PYTHONPATH:+:$PYTHONPATH}" "$repo/venv/bin/python" -m navigator "$@"
