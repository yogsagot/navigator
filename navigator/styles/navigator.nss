/*
 * What Navigator's screens are made of -- and deliberately not what colour
 * they are.
 *
 * Every value here is a variable, and this file defines none of them: the
 * numbers live in `themes/*.nss', each of which is a DOS Navigator `.PAL'
 * palette decoded by `tools/palconv.py'.  So this sheet does not parse on its
 * own, and is always loaded with a palette after it:
 *
 *     read(SCHEME_PATH, THEMES / "norton.nss")
 *
 * which is what `python -m navigator --theme norton' does.  The alternative --
 * carrying the default palette here as well -- would have meant one scheme
 * spelled out twice, hand-copied here and generated in `themes/default.nss',
 * and the two drifting the first time a slot was corrected.
 *
 * Most of what this file says is what it does not say: a part with no rule of
 * its own inherits the widget that paints it, so the panel footer, the error
 * line and an ordinary listing row need no declarations at all.
 *
 * There is no `bold' anywhere below, and that is not an omission.  DOS
 * Navigator has no bold: an attribute byte carries four bits of foreground, so
 * intensity is a colour and `white' is already the bright form of
 * `light_gray'.  Saying `bold' as well would double-brighten it on terminals
 * that render bold as bright, and the two panels would stop matching.
 */

Manager { fg: $desktop-fg; bg: $desktop-bg }

/* A panel's own colours are its listing colours, which is also what the frame
   and the fill inherit -- as in the original, where the frame and the interior
   of a file panel share a background and differ only in intensity. */
Panel               { fg: $panel-fg; bg: $panel-bg; border: single }
Panel:active        { border: double }

/* The path across the top frame. `TTopView.Draw' picks between these two on
   `sfSelected', which is this `:active'. */
Panel::title        { fg: $title-fg; bg: $title-bg }
Panel:active::title { fg: $active-title-fg; bg: $active-title-bg }

/* These two tie on specificity -- a class and a state each -- so source order
   is what settles a directory under the cursor, and the cursor has to come
   second. Both name `fg' and `bg', so the winner takes the row outright; were
   either to mention a property the other left out, the per-property cascade
   would carry that one property across from the loser. */
Panel::row.directory { fg: $directory-fg; bg: $directory-bg }
Panel::row:selected  { fg: $cursor-fg; bg: $cursor-bg }

/* One palette entry, two bars: Turbo Vision gives `TMenuView' and
   `TStatusLine' the same six colours (MENUS.PAS), and DOS Navigator never
   split them. Hence `$bar-' rather than a name that claims otherwise. */
MenuBar         { fg: $bar-fg; bg: $bar-bg }
MenuBar::hotkey { fg: $bar-key-fg; bg: $bar-key-bg }

KeyBar         { fg: $bar-fg; bg: $bar-bg }
KeyBar::number { fg: $bar-key-fg; bg: $bar-key-bg }
