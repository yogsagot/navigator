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
nav 0.0.1 from /home/you/.local/share/pipx/venvs/navigator-fm/lib/python3.12/site-packages/navigator (python 3.12.3)
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
