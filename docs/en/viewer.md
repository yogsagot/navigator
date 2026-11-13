# The viewer

`F3` shows the file under the cursor without changing it. It opens at once however large the file is.

## Keys

| Key | What it does |
|---|---|
| `Up`, `Down`, `PgUp`, `PgDn` | Scroll |
| `F2` | Wrap long lines, or stop wrapping |
| `F4` | Switch between text, hex and dump |
| `F5` | Go to an address |
| `F6` | Change the character filter |
| `F7` | Search; `Shift+F7` searches again, `Ctrl+F7` backwards |
| `Shift+F3` | Show a Markdown, HTML or similar file rendered, or as its source |
| `Shift+F4` | Edit the file |
| `Shift+F5` | Save the file under another name |
| `Shift+F6` | Choose the encoding the text is read in |
| `Ctrl+T` | Follow the end of a file that is growing |
| `Ctrl+G` | Show only the lines that match a text |
| `Alt+PgDn` | List the files viewed before |
| `Esc`, `F3` | Close the viewer |

The same commands are in the *View* menu, which is on the menu bar while a viewer is open.

In hex mode you can change bytes: type hex digits over them, or press `Tab` and type characters. `Shift+F2` writes
the changes to the file.

## What it shows specially

Some files open as something other than their text: Markdown, reStructuredText and HTML as a page, a PDF as its
text, a picture as a picture on a terminal that can draw one, and JSON, YAML, TOML and XML as a tree with
`Shift+F3`. The [Viewer types](settings.md#viewer-types) settings say which files.

A dBase, SQLite or CSV file opens as a table of records.

## Quick view

`Ctrl+Q` shows the file under the cursor in the other panel's place, and follows the cursor as it moves. `Tab`
moves the keyboard into the view, where the viewer's keys work.

## Searching a table

`F7` in the table searches the records for a text. `Shift+F7` repeats the search.

- *Text to search* is the text to look for.
- *Case sensitive* tells capital letters from small ones.
- *Scope*: *In cursor field* looks only in the column the cursor is in, *All fields* in every column.
- *Direction*: *Forward* from the cursor towards the last record, *Backward* towards the first, or *Entire scope*
  from the first record on.
