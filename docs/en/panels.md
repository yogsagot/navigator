# Panels

The file manager shows two panels side by side, each listing the files of one directory. One of them is active:
it has the cursor bar, and commands work on its files and usually offer the other panel's directory as the place
to put a result.

## Moving around

| Key | What it does |
|---|---|
| `Tab` | Switch to the other panel |
| `Up`, `Down`, `PgUp`, `PgDn`, `Home`, `End` | Move the cursor |
| `Enter` | Go into a directory or an archive, run a program, or open a file |
| `Backspace`, `Ctrl+PgUp` | Go to the parent directory |
| `Ctrl+\` | Go to the root directory |
| `Ctrl+R` | Read the directory again |
| `Alt+Backspace` | List the directories you have been in |
| `Alt+=` | Show the same directory in the other panel |
| `Ctrl+U` | Swap the two panels |

Typing letters writes on the command line under the panels; see [the command line](console.md).

A panel reads its directory again by itself when something changes in it.

## Views

`Ctrl+Y` goes through three views of a panel:

- *Simple*: names and sizes.
- *Detailed*: names with size, attributes, owner and date in columns. `Alt+K` chooses the columns.
- *List*: names alone, in several columns.

In the simple and detailed views `Left` and `Right` scroll long names. In the detailed view a click on a column's
title sorts by that column, and a second click reverses the order.

`Ctrl+H` shows or hides hidden files, and `Alt+I` shows or hides the lines under the listing.

## Sorting

`Alt+B` chooses the order of a panel: by name, extension, size, time, attributes, owner or type, each in either
direction, or unsorted. Directories are listed before files.

## Tagging files

Commands work on the tagged files, or on the file under the cursor when none is tagged.

| Key | What it does |
|---|---|
| `Ins`, or `Space` with an empty command line | Tag or untag the file and move down |
| `Gray +` | Tag the files that match a mask |
| `Gray -` | Untag the files that match a mask |
| `Gray *` | Invert the tags |
| `Ctrl+A` | Tag everything |

With the mouse, the middle button tags a file, and dragging with it tags every file passed. `Shift` or `Ctrl`
with a left click tags from the cursor to the file clicked.

The lines under the listing say how many files are tagged and their total size.

## Quick search

`Ctrl+S` starts a search by name: type the first letters and the cursor goes to the first name that begins with
them. `Ctrl+S` again goes to the next one. `Esc` ends the search; any other key ends it and does what it normally
does, so `Enter` goes straight into the directory found.

## Copying through the clipboard

`Ctrl+C` copies the selection and `Ctrl+X` cuts it; `Ctrl+V` in another directory pastes the files there, asking
as [Copy and move](file-operations.md#copy-and-move) do. `Esc` forgets the files. These keys work on the panel
while the command line is empty.

## The other side

The side that is not active can show something else in the panel's place:

| Key | What it shows |
|---|---|
| `Ctrl+T` | A tree of directories |
| `Ctrl+Q` | A quick view of the file under the cursor |
| `Ctrl+L` | Information about the directory, the disk and the file under the cursor |

The same key puts the panel back. `Ctrl+F1` and `Ctrl+F2` hide the left and the right side, `Ctrl+P` hides the
side that is not active, and `Alt+Left` and `Alt+Right` move the divider between the sides.

`Alt+F12` switches to Miller columns: a row of narrow columns, one for each directory on the way, with a preview
of what is under the cursor.

## More than one file manager

`Ctrl+F3` opens another file manager window. See [Windows](windows.md) for moving between windows.

## File masks

Several boxes take a file mask. A mask is one or more patterns separated by `;`, where `*` stands for any text and
`?` for any one character. A pattern that starts with `-` excludes what it matches, and the last pattern that
matches a name decides: `*;-*.bak` is every file except backups.

## Panel options

`Alt+S`, or *Panel > Setup Panel*, sets how the active panel lists its files. The same choices for every new panel
are on the *Panel defaults* page of the [settings](settings.md#panel-defaults).

- *Sort by* chooses the order: by name, extension, size, time, attributes, owner or type, or unsorted. *Reverse
  order* turns it round.
- *Directory length* counts each directory's size and shows it.
- *Current file*, *Selected files*, *Totals* and *Free space* choose the lines shown under the listing.
- *Files highlight* colours files by their type.
- *Executable first* and *Archives first* list those files before the others.
- *File mask* limits the panel to the files that match a [mask](#file-masks).

## Filter

`Alt+Del`, or *Panel > Selection > Advanced filter*, chooses which files the panel shows by their extensions. The
box lists `*` and one mask for every extension found in the directory.

- `Space` or `Ins` marks a mask and moves to the next. `+` marks all of them, `-` none, and `*` inverts the marks.
- *Show* makes the panel show the marked masks, or the one under the cursor when none is marked.
- *Hide* makes the panel leave them out.
- *Close* closes the box. It stays open after *Show* and *Hide*, so you can go on choosing.

Choosing `*` shows everything again.

## Find file

`Alt+F7`, or *File > Find*, searches for files by name and by what they contain.

- *File mask* is which names to look for. A plain word with no `*` and no dot finds every name that starts with it.
- *Text to find* limits the search to files that contain the text. Leave it empty to search by name alone.

### Options

- *Advanced search* also applies the limits set with the *Advanced* button.
- *Case sensitive* tells capital letters from small ones in the text.
- *Recursive search* looks in the subdirectories too.
- *Whole words* skips text that is part of a longer word.
- *Regular expression* reads the text as a regular expression, matched across lines.

### Scope

- *Entire disk* searches the whole disk the panel is on.
- *Current directory* searches the panel's directory.
- *All drives* searches every disk.

### The results

The files found are listed in the panel, titled *Find:* and the mask. You can view, edit, copy and delete them
there like any other files; the line under the panel says which directory each one is in. `Enter` on `..` goes
back to the directory you searched from.

### Advanced search

The *Advanced* button sets limits that apply while *Advanced search* is ticked:

- *Date is after* and *Date is before* limit the files by when they were changed. Dates are written
  year-month-day, such as `2026-01-31`.
- *Size is greater than* and *Size is less than* limit them by size.
- *Kind* limits them to executables, symbolic links, hidden files, read-only files, or broken links.

*Clear all* removes every limit.

### Replace in files

`Alt+Shift+F7` opens the same box with one more line, *Replace with*. It finds the files in the same way and
replaces the text in each of them.

## Make a list file

`Alt+L`, or *Panel > Make list file*, writes the names of the tagged files into a text file.

- *File name* is the file to write. If it is already there, you are asked whether to replace it or add to its end.
- *Action*, when filled in, turns the list into a script: one line per file, with the file's name put into the
  text you give. Several lines per file are separated by `;`.
- *Store path names to list file* writes each file's whole path, not its name alone.
- *Autodetermine necessity of path names* writes a path only for a file that is not in the list file's own
  directory.

In an action, these stand for parts of each file's name:

| You write | It becomes |
|---|---|
| `!` | The name without its extension |
| `.!` | The extension, with its dot |
| `!\` | The file's directory, ending in `/` |
| `!/` | The file's directory, without the final `/` |
| `!!` | A `!` |

An action with none of these gets the file's name added at its end: `cp` becomes `cp name`.
