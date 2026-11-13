# Archives

Navigator shows an archive as a directory: `Enter` on a zip or tar file goes inside it, and the files in it can be
viewed and copied out like any others. This page is about making an archive and unpacking one.

## Create an archive

`Shift+F1`, or *File > Archive > Create archive*, packs the selection into a new archive.

- *Archive to* is the archive's name. The line opens on the other panel's directory; a name with no directory makes
  the archive in the current one. *Tree* picks the directory from a tree. If the archive is already there, you are
  asked whether to add to it or replace it.
- *Archive type* chooses the format. The name's ending follows the type, and typing an ending chooses the type. A
  type that needs a program you do not have installed is greyed, and the line above the buttons says which.
- *Compression* trades time for size, from *None* to *Ultra*. Levels a format does not have are greyed; a plain
  TAR has none.
- *Password* encrypts the archive. It is available for ZIP and 7Z when 7-Zip is installed, and for RAR. You are
  asked to type it a second time.

Options:

- *Store pathnames* keeps each file's directories inside the archive, not its name alone.
- *Move files* deletes the files once they are in the archive.
- *Follow symlinks* packs what a link points to, not the link itself.

## Extract files

`Shift+F2` on an archive, or *File > Archive > Extract archive*, unpacks it into the directory you name. Inside an
archive, *Extract to* unpacks the selection.

- *Extract with path names* makes the archive's directories. Without it every file goes straight into the target
  directory.
- *Test only* checks the archive for errors and writes nothing.

*Tree* picks the target directory from a tree.
