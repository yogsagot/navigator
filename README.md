# Navigator project

Navigator (or nav) is a faithful recreation of the iconic DOS Navigator two-panel file manager for modern POSIX terminals.

## Installing

Navigator is published on PyPI as **`navigator-fm`** (the names `navigator` and `nav` were taken long ago;
`navfm` is an alias that installs the same thing). It needs Python 3.12 or newer, and pulls in one
dependency, `pyte`.

```sh
pipx install navigator-fm
nav
```

`pipx` is the right tool because it gives the application its own environment and still puts `nav` on your
PATH. `pip install --user` is refused on Debian and Ubuntu, whose Python is marked externally managed
(PEP 668); inside a virtualenv, plain `pip install navigator-fm` is fine.

Neither pip nor pipx updates anything on its own — `nav` stays on the version you installed until you run
`pipx upgrade navigator-fm`.

`nav --version` reports the version *and the directory it is running from*. That second half matters: if you
have Navigator installed more than one way, `~/.local/bin` comes before `/usr/bin` on most PATHs, and the
copy that runs may not be the one you just installed.

```
$ nav --version
nav 0.0.4 from /home/you/.local/share/pipx/venvs/navigator-fm/lib/python3.12/site-packages/navigator (python 3.12.3)
```

### Debian, Ubuntu

Packages are published from a signed repository, so `apt upgrade` carries new releases along with everything else.
Needs Ubuntu 24.04 or Debian 13 and later.

```sh
sudo install -m 0755 -d /usr/share/keyrings
sudo curl -fsSL -o /usr/share/keyrings/navigator-fm-archive-keyring.gpg \
    https://yogsagot.github.io/navigator/navigator-fm-archive-keyring.gpg

sudo tee /etc/apt/sources.list.d/navigator-fm.sources > /dev/null <<'EOF'
Types: deb
URIs: https://yogsagot.github.io/navigator/deb
Suites: stable
Components: main
Architectures: all amd64 arm64
Signed-By: /usr/share/keyrings/navigator-fm-archive-keyring.gpg
EOF

sudo apt update && sudo apt install navigator-fm
```

### Fedora, RHEL, Alma, Rocky

Needs Fedora 39 or RHEL 10 and later.

```sh
sudo rpm --import https://yogsagot.github.io/navigator/navigator-fm-archive-keyring.asc

sudo tee /etc/yum.repos.d/navigator-fm.repo > /dev/null <<'EOF'
[navigator-fm]
name=Navigator file manager
baseurl=https://yogsagot.github.io/navigator/rpm
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://yogsagot.github.io/navigator/navigator-fm-archive-keyring.asc
EOF

sudo dnf install navigator-fm
```

Run `nav --help` for the options; `--theme NAME` picks one of the eleven colour schemes, and `--list-themes`
names them.

It contains of three parts:

- **navkit** - the application core library.
    - defines Application class that holds async event-loop and orchestrates widget render on ANSI terminal
    - handles ANSI terminal - cell render, terminal events, keyboard and mouse events
    - defines a screen buffer where all the widgets render their contents and which is rendered to terminal on demand
    - defines Widget abstract class that has its own render() method that renders to screen buffer
    - defines observable attributes on widgets that when changed trigger update of other widget attributes that
      reference them
    - defines css-like style sheet library and style lookup engine (`*.nss` files)
- **navml** - custom markup language and widget library
    - defines a custom markup language in *.nml files heavily inspired by QML and Kivy frameworks – QML for the
      architecture, Kivy for the syntax, so blocks are made by indentation, and lines carry no semicolons
    - defines an *.nml file parser that translates it into a node graph suitable for python class code-generator
    - defines a python class code-generator that traverses node graph from parser
    - silently merges a code-generated python class with a handwritten python module with event handlers
    - overrides python import routine so a single import handles the merged class
    - defines a rich widget library to handle windows, buttons, menus, labels, etc., defines standard event handlers.
      Heavily inspired by Borland's TurboVision library
- **navigator** or nav - two panel file manager application
    - defines a Manager window that has two panels with file listings
    - defines View and Edit file windows
    - performs file operations over the selected files in the manager
    - uses file system handlers that enable file operations over ssh, smb, in zip files, etc.
    - defines a flexible plugin system to expand core functionality with third party plugins
    - carefully recreates the look and feel of classic DOS Navigator by Ritlabs
    - TETRIS
