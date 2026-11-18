# Macros

Navigator has two kinds of macro: keys you record and play back anywhere, and macros written in a file for the
editor.

## Key macros

A key macro is a recording of what you type. There are nine, numbered 1 to 9, and they are kept from one session
to the next.

| Key | What it does |
|---|---|
| `Ctrl+J` `R` `1` to `9` | Start recording into that macro |
| `Ctrl+J` `R` and any digit, while recording | Stop recording |
| `Ctrl+J` `1` to `9` | Play that macro |

Press the keys one after another: `Ctrl+J`, then `R`, then the digit. While a macro is being recorded, `>MACRO<`
is shown beside the clock.

Everything you type is recorded, and what you paste, in any window or dialog box. Recording cannot be started or
stopped while a dialog box is open, so open the box after you start and close it before you stop.

While a program is running in the console or in a command window, `Ctrl+J` goes to the program.

## Editor macros

An editor macro is a list of editor commands with a name. `Ctrl+J` `0` in the [editor](editor.md) lists the
macros for the file being edited and plays the one you choose.

The macros are in `macros.ini`, which *Options > Configuration > Macro file edit* opens. A section names the
files its macros are for, with masks separated by `;`. The section `[*]` is for every file.

```ini
[*]
MACRO Date and time
  InsertDate
  PRINT ' '
  InsertTime
ENDMACRO

[*.c;*.h]
MACRO Block
  PRINT '{'^M'}'
  MoveUp
ENDMACRO
```

Each line of a macro is one of these:

| Line | What it does |
|---|---|
| `PRINT 'text', n` | Types the text, `n` times; `n` may be left out |
| `GOTOXY x, y` | Moves the cursor to column `x` of line `y`, both counted from 0 |
| `GOTOX x`, `GOTOY y` | Moves to the column alone, or to the line alone |
| `MARK n`, `GOTO n` | Sets marker `n`, from 1 to 9, or goes to it |
| `Command, n` | Runs an editor command, `n` times |

In `PRINT`, text is written in single quotes, and `''` inside them is a quote. Outside the quotes `^M` is a
control character, here `Enter`, and `#13` is a character given by its code.

A command is written by DOS Navigator's name for it, such as `WordLeft`, `MoveUp` or `DelChar`, or by its name
in `keybindings.ini`, such as `word_left`. A name that is not known is passed over, and you are told which.

A line that starts with `;` is a comment.
