"""F4's model: DOS Navigator's editor (``MICROED.PAS``, ``EDITOR.PAS``) without its widgets.

What ``navigator/viewer.py`` is to F3, this package is to F4, and it is a
package rather than one module because the editor is several things the viewer
never had to be: a mutable text (:mod:`.document`), the mapping between that
text and the columns it paints (:mod:`.columns`), the edits and their undo
(:mod:`.buffer`), and the saving (:mod:`.save`).  Nothing here imports a widget,
so every rule is tested without an application.

**A file round-trips byte for byte**, which is the one deliberate departure
from DN underneath everything else: ``ReadBlock`` expanded tabs, ``ModifyLine``
trimmed trailing blanks, ``WriteBlock`` forced one line ending and the loader
split a line at 254 characters.  Here a tab stays a tab, a line keeps its own
terminator, and a byte that is not UTF-8 survives as a lone surrogate
(``surrogateescape``) and is drawn as its CP437 glyph, as the viewer draws it.
"""
