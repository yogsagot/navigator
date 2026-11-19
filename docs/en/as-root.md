# Working as root

When a step on your disk is refused because you lack the permission, Navigator can do it again as root. It asks
for your password through `sudo`, or lets `pkexec` ask, and remembers it for no longer than the step needs.

## The As root question

When copying, moving, erasing, renaming, making a directory or a link, changing attributes, saving in the editor
or reading a file is refused, the message offers *As root* beside *Skip* and *Cancel*. Choose it, give
your password, and the step is done again as root -- and so is every later step of the same operation, without
asking again.

Going into a directory you may not read asks the same question. Answered, the panel lists the directory as root:
its path is shown as `root:///path`, and copying, erasing, viewing, editing and the rest work there as anywhere
else. Commands that would run as you rather than as root, such as *Panelize* and *Show hard links*, are greyed
there. Going up into a directory you may read takes the panel back to the disk.

## Root access

*Utilities > Elevate root access* asks for the password once and keeps root access open: until it is closed,
a directory you may not read opens as root without asking, and the [console](console.md) runs a root shell that
follows the panel. While it is open, *ROOT* is shown on the menu bar beside the clock, and on the key bar when the
menu bar is hidden.

*Utilities > Close root access*, in the same place, or a click on *ROOT*, closes it: the panels that were
browsing as root go back to the disk, and the console goes back to your own shell.

Root access also closes by itself after it has not been used for a while, and always when Navigator quits.

## Settings

On the [System](settings.md#system) page of the settings:

- *Root access* chooses how to become root: *Auto* uses `sudo`, else `pkexec`; *sudo* and *pkexec* use that one;
  *Never offer* turns it off. With *Never offer*, or with neither program installed, nothing offers *As root*.
- *Keep root open while idle* is how many minutes root access stays open after its last step. With `0` it closes
  as soon as each operation ends.

Running Navigator as root already, nothing is offered: every step is root's.
