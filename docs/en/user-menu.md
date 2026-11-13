# The user menu and file associations

## The user menu

`F2` opens a menu of your own commands. Navigator looks for a file named `.navigator-menu.ini` in the panel's
directory and in each directory above it; that is the *local* menu. When there is none it uses the *global* one,
`menu.ini` in Navigator's configuration directory.

In the menu, `F2` switches between the local and the global menu, and `F4` opens the one shown in the editor.
*Options > Global menu definition* and *Local menu definition* edit them too.

### Writing a menu

```ini
# A comment
~S~how the file = less !.!

[Archive]
~P~ack this file = tar czf !.tar.gz !.!
-
~L~ist = tar tf !.!
```

- `Caption = command` is an item. Indented lines under it are more commands for the same item.
- `[Name]` starts a submenu, and `[Name/Inner]` one inside it.
- A line with only `-` is a separator.
- `~` before a letter makes it the item's hot key. A caption that starts with `F1` to `F12` and a space is chosen
  by that key.

These stand for the file under the cursor in the active panel:

| You write | It becomes |
|---|---|
| `!` | The name without its extension |
| `.!` | The extension, with its dot |
| `!.!` | The whole name |
| `!\` | The directory, ending in `/` |
| `!/` | The directory, without the final `/` |
| `!!` | A `!` |

The same with `$` in place of `!` stand for the file in the other panel, so write `$$` for a `$` of your own. `%1` is a file that lists the tagged
names of the active panel, and `%2` those of the other panel.

`%3` to `%9` are words you are asked for when the item runs. A line `<Title` gives the question a title, and
`<=text` fills in an answer to start from.

Names are quoted for the shell where they need it, so do not put quotes round them. The commands run in the
console's shell, as if you had typed them.

## File associations

Four more files in the configuration directory say which program handles which file. Each has a section per file
mask.

| File | What it decides | Edited from |
|---|---|---|
| `extensions.ini` | What `Enter` runs for a file | *Options > Extension file edit* |
| `viewers.ini` | What `F3` runs in place of the viewer | *Options > Viewers* |
| `editors.ini` | What `F4` runs in place of the editor | *Options > Editors* |
| `quickrun.ini` | What `Ctrl+Shift+F1` to `Ctrl+Shift+F10` run | *Options > Quick run file edit* |

`Alt+F3` and `Alt+F4` always use Navigator's own viewer and editor. Each file is written with examples the first
time Navigator starts.
