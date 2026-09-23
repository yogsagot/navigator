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
 * `bold' appears exactly once, on directory rows, and is a deliberate
 * departure rather than a transcription slip.  DOS Navigator had no bold at
 * all: an attribute byte carries four bits of foreground, so intensity is a
 * colour there and `white' is already the bright form of `light_gray'.  It is
 * set here because a listing reads better with directories emphasised.  The
 * cost is that a terminal rendering bold as bright will brighten a colour that
 * is already the bright one, so if directories ever stop standing out against
 * an ordinary row, this is the line to look at.
 *
 * Nowhere else, and nowhere in a theme: a palette defines colours only, so a
 * `.PAL' cannot introduce a property no DOS attribute could carry.
 */

Manager { fg: $desktop-fg; bg: $desktop-bg }

/* A panel's own colours are its listing colours, which is also what the frame
   and the fill inherit -- as in the original, where the frame and the interior
   of a file panel share a background and differ only in intensity. */
Panel               { fg: $panel-fg; bg: $panel-bg; border: single; icons: auto }
Panel:focused       { border: double }

/* The path across the top frame. `TTopView.Draw' picks between these two on
   `sfSelected', which is this `:active'. */
Panel::title        { fg: $title-fg; bg: $title-bg }
Panel:focused::title { fg: $active-title-fg; bg: $active-title-bg }

/* These two tie on specificity -- a class and a state each -- so source order
   is what settles a directory under the cursor, and the cursor has to come
   second. Both name `fg' and `bg', so the winner takes the row outright; were
   either to mention a property the other left out, the per-property cascade
   would carry that one property across from the loser. */
Panel::row.directory { fg: $directory-fg; bg: $directory-bg; bold: true }
Panel::row:selected  { fg: $cursor-fg; bg: $cursor-bg }

/* One palette entry, two bars: Turbo Vision gives `TMenuView' and
   `TStatusLine' the same six colours (MENUS.PAS), and DOS Navigator never
   split them. Hence `$bar-' rather than a name that claims otherwise. */
MenuBar         { fg: $bar-fg; bg: $bar-bg }
MenuBar::hotkey { fg: $bar-key-fg; bg: $bar-key-bg }

KeyBar         { fg: $bar-fg; bg: $bar-bg }
KeyBar::number { fg: $bar-key-fg; bg: $bar-key-bg }

/*
 * The widget library, bound to the slots DOS Navigator's Colors dialog
 * already names.  Every variable below has been carried in all eleven themes
 * since `tools/palconv.py' transcribed them, and was inert until there were
 * widgets to spend it on -- so what follows is a transcription rather than a
 * palette anybody chose.  `[NN]' is the slot number the theme files annotate.
 *
 * The rules live here rather than with the library, because `$dialog-*' is
 * *this application's* theme vocabulary: navml must not depend on the file
 * manager, and a library sheet naming these would not parse without a
 * Navigator palette behind it.  What navml ships instead is the contract --
 * which parts and which states each widget paints, declared on the classes.
 */

Window, Dialog        { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg }
Window::title         { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg }
Window::icon          { fg: $dialog-frame-icons-fg;      bg: $dialog-frame-icons-bg }

StaticText            { fg: $dialog-static-text-fg;      bg: $dialog-static-text-bg }

Label                 { fg: $dialog-label-normal-fg;     bg: $dialog-label-normal-bg }
Label:selected        { fg: $dialog-label-selected-fg;   bg: $dialog-label-selected-bg }
/* `bg' as well as `fg' on the two shortcut rules below, because `mono' gives
 * a shortcut a different background from an ordinary caption and the other
 * ten do not.  Naming only `fg' would read correctly in ten themes. */
Label::shortcut       { fg: $dialog-label-shortcut-fg;   bg: $dialog-label-shortcut-bg }

Button                { fg: $dialog-button-normal-fg;    bg: $dialog-button-normal-bg }
Button:default        { fg: $dialog-button-default-fg;   bg: $dialog-button-default-bg }
Button:focused        { fg: $dialog-button-selected-fg;  bg: $dialog-button-selected-bg }
Button:disabled       { fg: $dialog-button-disabled-fg;  bg: $dialog-button-disabled-bg }
Button::shadow        { fg: $dialog-button-shadow-fg;    bg: $dialog-button-shadow-bg }
/* The caption inherits the button, so only its marked letter needs a rule --
 * and it takes its background from whichever button rule won, which is the
 * per-property cascade doing exactly what it is for. */
Button StaticText::shortcut         { fg: $dialog-button-shortcut-fg }
Button:default StaticText::shortcut { fg: $dialog-shortcut-default-fg }
Button:focused StaticText::shortcut { fg: $dialog-shortcut-selected-fg }

InputLine             { fg: $dialog-input-normal-fg;     bg: $dialog-input-normal-bg }
InputLine:focused     { fg: $dialog-input-selected-fg;   bg: $dialog-input-selected-bg }
InputLine::selection  { fg: $dialog-input-normal-fg;     bg: $dialog-input-selected-bg }
InputLine::arrow      { fg: $dialog-input-arrow-fg;      bg: $dialog-input-arrow-bg }

CheckBoxes, RadioButtons     { fg: $dialog-cluster-normal-fg;   bg: $dialog-cluster-normal-bg }
CheckBoxes::item:selected,
RadioButtons::item:selected  { fg: $dialog-cluster-selected-fg; bg: $dialog-cluster-selected-bg }
CheckBoxes::shortcut,
RadioButtons::shortcut       { fg: $dialog-cluster-shortcut-fg; bg: $dialog-cluster-shortcut-bg }

/*
 * A scrollbar and a list have *two* sets of slots in the original -- `[35-36]'
 * and `[57-60]' under Dialogs, `[83-84]' under File Manager -- because the
 * same widget is a different colour inside a dialog from inside the desktop.
 * So the dialog rules are scoped to a dialog, which is also what keeps them
 * off `Panel': a panel is a `ListViewer' now, a type selector matches by
 * class name over the whole MRO, and `ListViewer { }' would otherwise tie
 * with `Panel { }' on specificity and win on source order.
 *
 * Two slots for a scrollbar, not three: the arrows and the thumb share one.
 * They are separate parts here so a sheet that wants to tell them apart can,
 * and this one does not.
 */
ScrollBar                { fg: $scrollbar-page-fg;  bg: $scrollbar-page-bg }
ScrollBar::arrow,
ScrollBar::thumb         { fg: $scrollbar-arrow-fg; bg: $scrollbar-arrow-bg }

Window ScrollBar         { fg: $dialog-scroll-bar-page-fg;  bg: $dialog-scroll-bar-page-bg }
Window ScrollBar::arrow,
Window ScrollBar::thumb  { fg: $dialog-scroll-bar-icons-fg; bg: $dialog-scroll-bar-icons-bg }

Window ListViewer            { fg: $dialog-list-normal-fg;     bg: $dialog-list-normal-bg }
Window ListViewer::row:selected { fg: $dialog-list-focused-fg; bg: $dialog-list-focused-bg }
Window ListViewer::divider   { fg: $dialog-list-divider-fg;    bg: $dialog-list-divider-bg }
