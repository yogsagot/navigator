# Utilities

## Process list

*Utilities > Process list* shows the running processes.

| Key | What it does |
|---|---|
| Typing, `F4` | Filter the list to the processes whose command, name, user or number contains the text; `Esc` clears it |
| `Ctrl+T` | Show the processes as a tree of parents and children |
| `Ctrl+H` | Show only your own processes |
| `Ctrl+P`, `Ctrl+U`, `Ctrl+E`, `Ctrl+L`, `Ctrl+Z`, `Ctrl+N` | Sort by number, user, state, CPU load, memory, command |
| `Left`, `Right` | Scroll long commands |
| `F3` | Show the details of a process |
| `F7` | Send a signal you choose |
| `F8`, `Del` | End the process, after asking |
| `Ctrl+R` | Read the list again |

A click on a column's title sorts by it. When a signal is refused for want of permission you are offered to send
it as root.

## Services

*Utilities > Services* lists the system's services and controls them, through systemd, OpenRC, runit or SysVinit.

| Key | What it does |
|---|---|
| `Enter` | Show the details of a service |
| `F3` | Show its log, and follow it |
| `F4` | Edit its configuration |
| `F5`, `F6`, `F7` | Start, restart, reload |
| `F8`, `Del` | Stop, after asking |
| `Ctrl+E`, `Ctrl+D` | Enable and disable starting at boot |
| `Ctrl+U` | Show your own services |
| `Ctrl+A` | Show units of every type |
| `Ctrl+S` | Filter the list |
| `Ctrl+R` | Read the list again |

Changing a system service usually needs root, which you are offered.

## System monitor

*Utilities > System monitor* shows the load on each processor, the memory and swap in use, and the temperatures
and fan speeds the machine reports.

## Edit the environment

*Utilities > Edit environment* shows the environment variables that programs started from Navigator are given, and
lets you change them.

- *Variables* lists the names. The value of the one under the cursor is on the *Value* line, where you can edit
  it.
- *Rename* gives the variable another name.
- *Append* adds a new variable.
- *Delete* removes the variable under the cursor.
- *OK* keeps the changes; *Cancel* drops them all.

The changes reach the programs Navigator starts from then on: the external viewer and editor, the user menu's
commands, and the shell in the console. They last until you leave Navigator.
