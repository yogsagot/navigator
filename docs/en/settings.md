# Settings

*Options > Settings* holds every setting on fifteen pages. `Ctrl+PgUp` and `Ctrl+PgDn` change pages; the entries
under *Options > Configuration* and *Options > File Manager* open the box on their own page. Resting the mouse on
an option shows what it does.

*OK* applies the changes at once and writes them to `navigator.ini`. *Cancel* drops them.

## System

- *Internal editor* and *Internal viewer*: `F4` and `F3` use Navigator's own editor and viewer. Off, they run the
  program named in `$EDITOR` and `$PAGER`.
- *Use system clipboard*: copy to and paste from the desktop's clipboard. Off, Navigator keeps a clipboard of its
  own.
- *Show hidden files*: a new panel shows hidden files. `Ctrl+H` switches one panel.
- *Sync after copying*: each copied file is written through to the disk before it counts as done.
- *Use internal terminal*: `Ctrl+O` shows the console inside Navigator. Off, it hands the whole terminal to the
  shell.
- *Command windows zoomed* and *Command windows modal*: how a command run in a window of its own opens.
- *Temporary directory*: where temporary files go. Empty means `$TMPDIR`.
- *Unexpected failures*: an unexpected error either shows a message with its details, or quits Navigator and
  prints them.
- *Report a stall after*: how many seconds Navigator may stop responding before the reason is written to
  `errors.log`.
- *Root access*: how a step that was refused permission can be done again as root: through `sudo`, through
  `pkexec`, or never.
- *Keep root open while idle*: how many minutes root access stays open after its last use.

## Startup

- *Auto run User Menu*: the user menu (`F2`) opens when Navigator starts.
- *Clear History*: history entries that are not pinned are removed at each start.
- *Inactivity hour exit*: Navigator quits after an hour with no key or click.
- *Autosave Desktop*: the windows are saved when you quit and put back at the next start.
- *Preserve directory*: the active panel keeps its directory after a command, and in a restored desktop.

## Interface

- *Clock*, *Hide menu bar*, *Hide status line*: the clock on the menu bar, the menu bar itself until `F10`, and
  the key bar on the bottom line.
- *ESC for user screen*: `Esc` on an empty command line shows the console until the next key.
- *Hide Command Line* and *Auto hide Command Line*: hide the command line always, or while it is empty.
- *Block Insert Cursor*: a block cursor on the command line.
- *Store editor position* and *Store viewer position*: a file reopens in the window, and at the place, it was
  left in.
- *Track editing history*, *Track viewing history*, *Track directories*: keep the lists that `Alt+PgUp`,
  `Alt+PgDn` and `Alt+Backspace` show.
- *History size*: how many entries each history list keeps.
- *Tooltip delay (ms)*: how long the mouse rests before a tooltip shows; 0 for none.
- *Language*: the language of captions and messages.
- *Colours*: how many colours to send to the terminal.
- *Glyphs*: which characters the terminal's font is assumed to have: plain ASCII, Unicode, or a Nerd Font's icons.
- *Dim behind dialogs*: what is behind a dialog is painted faint.
- *Marks*: how check boxes and radio buttons are drawn.
- *Text direction*: left to right, right to left, or as the language reads.
- *Settings tabs*: where this box shows its tabs.
- *Window strip*: whether the open windows are listed on the menu bar, by number or with their titles.

## Confirmations

Each box makes Navigator ask before the action: erasing one file, erasing several, erasing a directory that is not
empty, erasing read-only files, creating a directory that a copy names, a drag-and-drop, quitting, saving in the
editor, deleting a bookmark, and closing a command window whose command is still running.

## Savers

A screen saver takes over the screen after a time with no key or click.

- *Selected savers* take turns. *Add* moves one in from *Available savers*, and *Remove* takes it out.
- *Time* is how long to wait, or *Never*.
- *Use mouse to call saver*: moving the pointer into the top right corner starts a saver at once; while it is in
  the bottom right corner none starts.

## Country

- *Date format*: the order dates are written in, or *Custom* with the format written out on the *Custom format*
  line.
- *Time*: a 12-hour or a 24-hour clock.
- *Week starts*: the first day of the week in calendars.
- *Calendar system* and *Calendar view*: which calendar the Calendar window shows, and whether it stands beside
  the Gregorian one.

*Example* shows a date and time written as chosen.

## Editor/Viewer

What a new editor or viewer window starts with. Most of the editor's can be switched for one window from its
*Options* menu.

Editor options:

- *Create backup files*: saving with `F2` keeps the old file as `NAME.bak`.
- *Backspace unindents*: `Backspace` in the leading blanks goes back to the indent of a line above.
- *AutoBrackets*: typing `(`, `{` or `[` also types its partner.
- *Auto indent*: `Enter` indents the new line as the one above.
- *Autowrap* and *Justify on wrap*: a line typed past the right margin is wrapped, and the line left behind is
  widened to the margin.
- *Vertical blocks*: blocks are marked as columns.
- *Optimal fill*: blanks that reach a tab stop are written as a tab.
- *Highlight line* and *Highlight column*: the cursor's line and column are highlighted.
- *Persistent blocks*: the block stays marked when the cursor moves. *Overwrite blocks*, with that off: typing
  and pasting replace the block.
- *Lock file*: the editor holds a lock on its file that other programs can see.
- *Tab key inserts tabs*: `Tab` inserts a tab character, not spaces.
- *Line numbers*: lines are numbered down the left.
- *Option strip*: the bottom frame shows the window's options, and a click switches one.

Viewer options: *Hex mode* opens files in hex, *Wrap lines* wraps long lines, and *Option strip* is as the
editor's.

- *Left margin*, *Right margin*, *Paragraph*: the margins for [paragraph formatting](editor.md#margins).
- *Tab size*: the width of a tab.
- *Line divisor (editor)*: the line ending a new file is given.
- *Fallback encoding*: what the editor reads a file as when it is not UTF-8.

## Viewer types

Which files `F3` shows as something other than their text: Markdown, reStructuredText and HTML as a page, PDF as
its text, pictures as pictures, CSV and TSV as a table, and structured files (JSON, YAML, TOML, XML) as a tree.
Each has a box to switch it on and a line of [file masks](panels.md#file-masks) saying which files it applies
to. *SQLite databases* is the mask for files to open as a database.

## File panels

Behavior:

- *Auto change directory*: the panel follows the cursor in the tree beside it.
- *Drag-and-drop from columns*: files can be dragged out of a panel with the mouse.
- *Beep after copy*: the terminal's bell rings when a copy ends.
- *ENTER opens archive*: `Enter` on an archive goes inside it as a directory.
- *ENTER mounts disc images*: `Enter` on an `.iso` or `.img` file mounts it and opens it.
- *SPACE toggles selection*, *DEL erases file(s)*, *BS - go to upper directory*: these keys work on the panel
  while the command line is empty.
- *Use ←/→ keys*: the arrows, `Home` and `End` edit a command line that has text. Off, they do so with `Shift`.
- *Auto refresh panels*: a panel reads its directory again when it changes on the disk.
- *F8 moves to Trash*: `F8` moves files to the Trash instead of erasing them.
- *Pass other files to desktop*: `Enter` on a file with no program set for it opens it in the desktop's
  application.
- *Return to last cursor position*: coming back to a directory puts the cursor where it was left.
- *Miller column width*: the width of a column in the Miller view.

Display:

- *Column titles*: a heading row over the columns.
- *Info divider*: a line over the totals under the listing.
- *Tag character* and *Tag sign*: a tagged file is marked with a sign, and which sign.
- *Link target line*: a line under the panel shows where a symbolic link points.
- *Option flags*: the bottom frame shows the panel's options, and a click switches one.
- *Git status*: in a git work tree, each file's status, and the branch in the title.

*Right button* chooses what the right mouse button does in a panel: open the context menu, or tag files.
*Remember directory settings* chooses which directories keep their own sort order, view, columns and file mask.

## Info panel

Which lines the information panel (`Ctrl+L`) shows: the directory's name, its totals, the file under the cursor,
media details, the volume's size, free space and label, the machine's memory, and the directory's information
file.

## Panel defaults

How the panels of a new file manager start.

- *Sort by* and *Reverse order*: the order files are listed in.
- *Directory length*: each directory's size is counted and shown.
- *Current file*, *Selected files*, *Totals*, *Free space*: the lines under the listing.
- *Files highlight*: files are coloured by their type.
- *Executable first* and *Archives first*: those files are listed before the others.
- *Left panel in new Manager will be*: a file panel, the information panel, a tree, or nothing.
- *Panel mode*: the simple, detailed or list view.

## Columns

Which columns a panel shows, set apart for the disk, for a *Find:* listing, and for an archive.

## Highlight

The [file masks](panels.md#file-masks) of the five groups that the panels colour: images, audio and video,
documents, source code, and temporary files.

## Communications

- *Keep-alive every*: how often a message is sent to keep a connection to a server open.
- *Connecting waits*: how long to wait for a server to answer.
- *Close an idle connection*: how long an unused connection stays open.
- *Look for changes every*: how often a server's directory is checked for changes.
- *A fetched file a program changed goes back*: whether such a file is uploaded again: after asking, always, or
  never.
- *Desktop integration*: which desktop's services are used for volumes, links and opening files.
- *Remote shell's ssh options*: words added to the `ssh` command of every remote shell.
- *Notify when a long operation ends unwatched*: how the desktop is told that a long operation has ended while
  the terminal was in the background.

## Tools

- *Age identity files*: the key files `age` decrypts with.
- *Process list reads every*, *Services read every*, *System monitor reads every*: how often those windows
  refresh.
- *Service manager*: which service manager the Services window talks to.
- *Journal lines F3 shows first*: how much of a service's log `F3` opens on.
