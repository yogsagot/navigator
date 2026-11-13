# The command line and the console

Under the panels is a command line, and behind the windows is a console: a terminal in which your shell runs.

## The command line

Whatever you type while a panel has the keyboard goes to the command line. `Enter` runs it in the shell, in the
active panel's directory, and the output appears in the console.

| Key | What it does |
|---|---|
| `Enter` | Run the command |
| `Ctrl+Enter` | Put the name of the file under the cursor on the line |
| `Ctrl+E`, `Ctrl+X` | Recall the previous and the next command |
| `Tab` | Complete the word being typed, when the line has text |
| `Esc` | Clear the line |

While the line has text, `Left`, `Right`, `Home` and `End` edit it. `Enter` on a program in a panel runs it.

After a command the panels read their directories again, and the active panel follows the shell if the command
changed directory.

## The console

`Ctrl+O` hides the windows and shows the console; `Ctrl+O` again brings them back. While the windows are hidden
the keys go to the shell, or to the program running in it.

`Shift+PgUp` and `Shift+PgDn` scroll back through what the console has shown, and `Shift+Up` and `Shift+Down`
scroll by a line.

While a program is running in the console it gets every key, `F1` and `F10` included; leave the program its own
way first.
