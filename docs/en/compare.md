# Comparing

## Compare directories

*Panel > Compare directories* compares the files of the two panels by name.

- *Compare size*, *Compare time*, *Compare attributes* and *Compare contents* choose what makes two files of the
  same name count as the same. Only *Compare contents* reads the files, and takes longer.
- *Select* tags, in each panel, the files with no match in the other. Copying the tagged files across brings the
  other directory up to date.
- *Unselect* removes the tags from those files instead.
- *Window, recursive* compares the directories with everything inside them, and opens the Synchronize window.

## Synchronize

The Synchronize window lists every file that is on one side only or differs, the left panel's directory on the
left. Each row has an action: copy to the right, copy to the left, delete, or skip. The window proposes one, and
the *Synchronize* menu changes it for the row under the cursor or for all rows at once.

- *Synchronize*, `F5`, carries out the actions, asking first.
- *Compare files*, `Enter` or `F3`, shows the two files of the row side by side.
- *Compare again*, `Ctrl+R`, reads both directories again.
- *Show left only*, *Show right only*, *Show different* and *Show identical* choose which rows are listed.
- *Tree view*, `Ctrl+T`, lists the rows as a tree of directories.
- *Options* sets how files are compared, and a [file mask](panels.md#file-masks) for which files are looked at.

## Compare files

*File > Compare files* shows two files side by side with their differences marked. It takes the two tagged files
of the active panel. With none tagged it takes the file under the cursor and the file of the same name in the
other panel, or, when there is none of that name, the file under the other panel's cursor.
