# Navigator project

This project is a faithful recreation of iconic DOS Navigator two panel file manager for modern POSIX terminals.

It contains of three parts:

- **navkit** - the application core library.
    - defines Application class that holds async event-loop and orchestrates widget render on ANSI terminal
    - handles ANSI terminal - cell render, terminal events, keyboard and mouse events
    - defines screen buffer where all the widgets render their contents and which is rendered to terminal on demand
    - defines Widget abstract class that has it's own render () method that renders to screen buffer
    - defines observable attributes on widgets that when changed trigger update of other widget attributes that
      reference them
    - defines *.css like style sheet library and style lookup engine
- **navml** - custom markup language and widget library
    - defines a custom markup language in *.nml files heavily inspired by QML and Kivy frameworks
    - defines an *.nml file parser that translates it into node graph suitable for python class code-generator
    - defines a python class code-generator that traverses node graph from parser
    - silently merges code-generated python class with hand written python module with event handlers
    - overrides python import routine so single import handles merged class
    - defines a rich widget library to handle windows, buttons, menus, labels etc, defines standard event handlers.
      Heavily inspired by Borland's TurboVision library
- **navigator** or nav - two panel file manager application
    - defines a Manager window that has two panels with file listings
    - defines View and Edit file windows
    - performs file operations over the selected files in manager
    - utilizes file system handlers that enable file operations over ssh, smb, in zip files etc
    - defines a flexible plugin system to expand core functionality with 3dr party plugins
    - carefully recreates look and feel of classic DOS Navigator by Ritlabs
    - TETRIS