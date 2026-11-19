# Starting Navigator

The command is `nav`:

```sh
nav [LEFT] [RIGHT] [options]
```

`LEFT` and `RIGHT` are the directories the two panels open on. With one, both panels open there; with none, both
open on the current directory. Either can be an address of a place other than the disk, such as
`sftp://user@host/dir`, `ftp://host/`, `smb://host/share` or `s3://s3.amazonaws.com/bucket`; see
[Places other than the disk](drives.md).

An option given on the command line holds for that session only. It wins over the
[settings](settings.md) and is never written back to them.

## Files and places

| Option | What it does |
|---|---|
| `-e FILE`, `--edit FILE` | Opens the file in the [editor](editor.md) at the start. Give it more than once for more files. A name that does not exist yet is made when you save |
| `--config PATH` | Reads and saves the settings in another file than `~/.config/navigator/navigator.ini` |
| `--database PATH` | Keeps the histories and bookmarks in another file than `~/.local/state/navigator/navigator.db` |
| `--version` | Prints the version and which copy of Navigator is installed, and exits |

The files that sit beside `navigator.ini` -- the [user menu and file associations](user-menu.md), the key
bindings, the palettes -- do not move with `--config`: they stay in `~/.config/navigator`.

## Colours and characters

| Option | What it does |
|---|---|
| `--theme NAME` | Uses another colour scheme |
| `--list-themes` | Prints the names of the colour schemes, and exits |
| `--palette dos` | Shows each colour as DOS Navigator's VGA card showed it, whatever the terminal's own colour scheme |
| `--palette terminal` | Leaves the sixteen colours to the terminal's own colour scheme |
| `--reprogram-palette` | Sets the terminal's sixteen colours to DOS's while Navigator runs, for a terminal that cannot be given colours any other way |
| `--colors DEPTH` | How many colours the terminal shows: `mono`, `8`, `16`, `256` or `truecolor`. `auto` goes by `$COLORTERM` and `$TERM` |
| `--glyphs SET` | Which characters the terminal's font draws: `ascii` draws frames with `+` and `-`, `unicode` draws boxes, `nerd` adds an icon beside each file name for a Nerd Font. `auto` guesses |
| `--marks LOOK` | How check boxes and radio buttons look: `dos` is `[X]` and `(•)`, `brackets` is `[✓]` and `(●)`, `boxes` has no brackets |
| `--charset NAME` | The character set of a terminal that is not UTF-8, such as `koi8-r`, `cp866` or `iso8859-2`. Without it the locale's is used |
| `--graphics HOW` | How the viewer draws a picture: `kitty`, `sixel`, or `none` to show its bytes. Without it the terminal is asked |
| `--no-dim-modal` | Leaves what is behind a dialog box at full colour, rather than faint; `--dim-modal` turns it back on |

[Keys and colours](customizing.md#colours) has more about themes.

## Language and direction

| Option | What it does |
|---|---|
| `--language CODE` | The language of captions and messages, such as `lv`, `ru`, `ja` or `en`. Without it the settings' *Language* is used, else `$LANG` |
| `--direction auto` | Mirrors the screen when the language is written right to left, such as Hebrew or Arabic. Without the option the settings' *Text direction* is used, which starts as this |
| `--direction rtl` | Mirrors the screen whatever the language, so that it reads from right to left |
| `--direction ltr` | Never mirrors the screen |
| `--bidi app` | Navigator lays out right-to-left text itself before sending it. Without the option the terminal is recognised and the right way chosen |
| `--bidi words` | Each right-to-left word is sent reversed, for a terminal such as kitty that turns it round again |

The same choices are on the [Interface](settings.md#interface) page of the settings.

## When something goes wrong

| Option | What it does |
|---|---|
| `--on-error dialog` | An unexpected error shows a box with its details, and you can go on |
| `--on-error crash` | An unexpected error quits Navigator and prints its details |

Either way the error is added to `errors.log`, in `~/.local/state/navigator` even when `--database` puts the
database elsewhere. The [System](settings.md#system) page of the settings has the same choice.

## Inside Navigator

Typing `nav` on Navigator's own command line does not start a second copy: it says that Navigator is already
running and that `Ctrl+O` returns to it.
