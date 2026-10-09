# Navigator project

Navigator (or nav) is a faithful recreation of the iconic DOS Navigator two-panel file manager for modern POSIX terminals.

<!-- screenshot:begin -->
![Navigator, 80x24](https://raw.githubusercontent.com/yogsagot/navigator/master/docs/screenshot.svg)

<details><summary>The same screen, as text</summary>

```text
  ≡  File  Disk  Utilities  Panel  Manager  Options  Window                12:34
┌─[■]───────────── . ──────────────────┐┌──────────────── src ─────────────[↕]─┐
│/bin                               DIR││/..                            UP--DIR│
│/docs        ╔═════════════════════ About ══════════════════[■]═╗          DIR│
│/src         ║                                                  ║          DIR│
│/tests       ║                    Navigator                     ║          DIR│
│ .gitignore  ║                  Version 0.0.4                   ║            0│
│ config.nss  ║                                                  ║          13K│
│ LICENSE     ║ A recreation of the DOS Navigator two-panel file ║           9K│
│ Makefile    ║           manager for POSIX terminals            ║          18K│
│ navigator.lo║                                                  ║          22K│
│ pyproject.to║   Juris Krumgolds <juris.krumgolds@gmail.com>    ║             │
│ README.md   ║                   License: MIT                   ║             │
│ setup.cfg   ║                                                  ║             │
│             ║      https://github.com/yogsagot/navigator       ║             │
│             ║                                                  ║             │
│             ║                   ▶   OK   ◀▄                    ║             │
│             ║                    ▀▀▀▀▀▀▀▀▀▀                    ║             │
│             ║                                                  ║             │
│─────────────╚══════════════════════════════════════════════════╝─────────────│
│   412,316,860,416 free bytes on /    ││   412,316,860,416 free bytes on /    │
└──────────────── bin ─────────────────┘└───────────────── .. ─────────────────┘
juris@juris-dev:~/development/navigator$
 F1 Help  F2 User  F3 View  F4 Edit  F5 Copy  F6 Ren  F7 MkDir  F8 Del  F10 Menu
```

</details>
<!-- screenshot:end -->

It consists of three parts:

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
    - lets a component be written as markup, as python, or as both -- a widget class generated from `*.nml` and a
      hand-written module of event handlers are two halves of one class, and either half may be absent
    - keeps an event handler written in markup to a single line taking one argument, always named `event`, and always
      consuming the event it handles -- anything longer, or a handler that lets the event through, is a method in the
      hand-written half that the markup line calls, so a document stays a description of a tree
    - extends python's import machinery so that one `import` yields the component whichever way it was written, and
      the hand-written half never has to name the generated one
    - defines a widget library modelled on Borland's TurboVision: windows, dialogs, buttons, static text, labels,
      input lines, check boxes, radio buttons, scroll bars and list viewers. Its widgets, their parts and their
      states are transcribed from DOS Navigator's own colour table rather than invented, so every one of the eleven
      themes already knows what colour they are.
- **navigator** or nav - two panel file manager application
    - defines a Manager window that has two panels with file listings
    - defines View and Edit file windows
    - performs file operations over the selected files in the manager
    - uses file system handlers that enable file operations over ssh, smb, in zip files, etc.
    - defines a flexible plugin system to expand core functionality with third party plugins
    - carefully recreates the look and feel of classic DOS Navigator by Ritlabs
    - Falling blocks game from late Soviet Union

Run `nav --help` for the options; `--theme NAME` picks one of the eleven colour schemes, and `--list-themes`
names them.
