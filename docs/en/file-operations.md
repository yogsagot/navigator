# File operations

Copying, moving, linking, splitting and encoding work on the selection: the tagged files of the active panel, or the
file under the cursor when nothing is tagged. Most of them open on the other panel's directory as the place to put
the result.

## Copy and move

`F5` copies the selection and `F6` renames or moves it. Both open the same box: a line saying where to, the copy
modes, and four options.

### Where to

What you type on the line decides what happens:

| You type | What it means |
|---|---|
| A directory that exists, or a name ending in `/` | The files go into that directory |
| A name with `*` or `?` | Each file is renamed by that mask, where it is going |
| Any other name, with one file selected | The file's new name |
| Any other name, with several files selected | A directory to create and copy into |

A mask is applied to the name and the extension separately: `*.bak` gives every file the extension `bak`. A mask
with no dot covers the whole name, so `*` keeps each name as it is.

`F10`, or the *Tree* button, picks the directory from a tree. `Down` on the line opens the history of the places
you copied to before.

### What to do with files that are already there

| Mode | What it does |
|---|---|
| *Overwrite all existing files* | Replaces them without asking |
| *Append to all existing files* | Adds each file to the end of the one already there |
| *Ask for overwrite* | Asks for each one. The answer can be made to stand for all the rest |
| *Skip all existing files* | Leaves them alone and copies the others |
| *Refresh old files* | Replaces a file only when the one being copied is newer |

When it asks, *Rename* lets you give the copy another name instead.

### Options

- *Check free disk space* stops before copying when the target has too little room.
- *Preserve attributes* keeps permissions, owner and times on the copies. What could not be kept is reported; the
  copy itself still succeeds.
- *Follow symlinks* copies what a link points to, not the link itself.
- *Remove source files* deletes the originals once they are copied, which makes the copy a move.

The mode and the options are remembered until you leave Navigator.

### While it runs

The progress box shows the speed and the time left. *Background* sends the copy away so you can keep working: a
percentage appears on the menu bar, and a click on it brings the box back. If the copy has a question while it is
away, the percentage shows a `?` and waits for you. *Stop* asks before abandoning the copy.

Files that were copied lose their tags; files that were skipped keep them.

`Ctrl+Z` takes back the last copy, move or rename. A copy is removed only if nothing has changed it since.

## Make a directory

`F7` makes a directory in the active panel. Type a path such as `a/b/c` to make every directory on the way, or
several names separated by `;` to make several.

## Erase

`F8`, or `Del` with an empty command line, erases the selection after asking. `Shift+F8` erases the file under
the cursor whatever is tagged.

- *Recursive delete* erases directories with everything in them without asking about each one.
- *Move to Trash* is shown when the [Trash](drives.md#the-trash) is in use. Unticked, the files are erased for
  good.

Without *Recursive delete* you are asked about a directory that is not empty, and about files you cannot write
to; each question can be answered for all the rest. Which questions are asked at all is set on the
[Confirmations](settings.md#confirmations) page of the settings.

A long erase can be sent to the background, as a copy can.

## File attributes

`Alt+E` changes the attributes of the selection. Only what you change is applied, so files that differ in other
ways keep their differences. *Recurse* applies the change to everything inside the directories as well.

- *Mode* has the permissions: a grid of read, write and execute for the owner, the group and others, the same as
  an octal number, the owner and group, and the date and time. In the grid `R`, `W` and `X` tick a whole row.
- *ACL* lists the access control entries beyond the mode, and adds, edits and removes them.
- *Xattrs* lists the extended attributes.
- *Flags* has the file system's flags, such as immutable and append-only.

A box that shows `?` means the files differ there; leave it alone to keep each file as it is.

## Links

`Shift+F5` makes links to the selection in the directory you name.

- *Symbolic link* makes a small file holding the path of the original. It can point to a directory, and to another
  disk.
- *Hard link* gives a file a second name. It works only for files, and only on the same file system.
- *Relative link* writes the path relative to the link, so the link and the original can be moved together. It
  applies to symbolic links only.

*File > Links* has more: editing where a link points, making links relative or absolute, tagging broken links, and
showing every name a hard-linked file has.

## Split and combine

*File > Split/combine* works on the file under the cursor, and the file's name decides which of the two it does.

### Splitting

Any ordinary file is split into parts named `NAME.001`, `NAME.002` and so on, in the directory you name.

- *Part size* is the size of each part: a number of bytes, or a number followed by `K`, `M` or `G`, such as `100M`
  or `1.44M`.
- *Write checksum file (.crc)* also writes `NAME.crc`, which holds the file's name, size and checksum. With it, the
  combined file can be checked.

A file no larger than one part is not split. Total Commander, Double Commander and 7-Zip can combine these parts.

### Combining

On a part (`NAME.001`) or on the `NAME.crc` of a set, the command puts the file back together in the directory you
name. It reads the parts in order until one is missing. With a `.crc` file it also checks the result; if the
checksum does not match, the file is kept and you are told.

## UU encode and decode

UU encoding turns any file into plain text that can be sent where only text is allowed.

### Encoding

`Ctrl+F7` encodes the file under the cursor into `NAME.uue`. A large file is written in sections, one file each.

- *Prefixes* add lines before the data: the file's date and time, the character table used, and statistics.
- *Checksum level* adds checksums so that damage can be found when decoding: none, of the whole file, of each
  section, of each line, or the 64-bit one.
- *Lines per section* is how many lines of data go into one section.
- *Target file format* chooses how lines end: as on DOS, or as on UNIX.

### Decoding

`Ctrl+F8` decodes the file under the cursor into the directory you name. One file may hold several encoded files
and their sections in any order.

- *Check existing files* asks before replacing a file that is already there.
- *Display error messages* shows each error found in the data.
- *Save broken files* writes a file even when its data was damaged.
