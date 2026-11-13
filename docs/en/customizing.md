# Keys and colours

## Key bindings

*Options > Configuration > Key bindings* changes which key does what. The keys are listed in sections, one for
each place they work in: everywhere, the file manager, the editor, the viewer, dialogs and so on.

Choose a command and press the key you want for it.

*Save* writes the whole set to a file, and *Load* reads one. Navigator comes with four sets: its default, and
sets after WordStar, DOS Navigator 1.51 and Emacs.

The bindings are kept in `keybindings.ini` in the configuration directory. Keys that move the cursor in lists and
in text are fixed.

## Colours

*Options > Colors* changes the colours of the theme in use.

- *Group* and *Item* choose what to colour.
- *Foreground* and *Background* choose from the sixteen colours; the lines beside them take any colour, as a name
  or as `#rrggbb`.
- The five boxes set bold, dim, italic, underline and reverse. A box showing `?` leaves the attribute as the item
  inherits it.

The screen follows as you change things. *OK* keeps the changes for this theme; *Cancel* puts everything back.

*Store palette* saves the colours as a theme of your own, which `--theme` and *Load palette* then find. *Load
palette* takes the colours of another theme.

To use another theme, start Navigator with `--theme NAME`; `--list-themes` names them.
