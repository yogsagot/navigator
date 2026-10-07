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

Shell { fg: $desktop-fg; bg: $desktop-bg; bold: $desktop-bold; dim: $desktop-dim; italic: $desktop-italic; underline: $desktop-underline; reverse: $desktop-reverse }

/* A window on the desktop takes the File Manager's frame slots [80-82]: the
   one window that exists is the file manager, and the frame colours are what
   DOS Navigator's CDoubleWindow palette gives it.  The active window is drawn
   double, as a focused panel is. */
Window              { fg: $frame-fg; bg: $frame-bg; border: single; bold: $frame-bold; dim: $frame-dim; italic: $frame-italic; underline: $frame-underline; reverse: $frame-reverse }
Window:active       { fg: $active-frame-fg; bg: $active-frame-bg; border: double; bold: $active-frame-bold; dim: $active-frame-dim; italic: $active-frame-italic; underline: $active-frame-underline; reverse: $active-frame-reverse }
Window::title       { fg: $frame-fg; bg: $frame-bg; bold: $frame-bold; dim: $frame-dim; italic: $frame-italic; underline: $frame-underline; reverse: $frame-reverse }
Window:active::title { fg: $active-frame-fg; bg: $active-frame-bg; bold: $active-frame-bold; dim: $active-frame-dim; italic: $active-frame-italic; underline: $active-frame-underline; reverse: $active-frame-reverse }
Window::icon        { fg: $frame-icon-fg; bg: $frame-icon-bg; bold: $frame-icon-bold; dim: $frame-icon-dim; italic: $frame-icon-italic; underline: $frame-icon-underline; reverse: $frame-icon-reverse }

/* The calculator is a dialog DN put on the desktop as a window: a dialog's
   colours, its frame single while another window is in front. */
CalculatorWindow               { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg; bold: $dialog-frame-background-bold; dim: $dialog-frame-background-dim; italic: $dialog-frame-background-italic; underline: $dialog-frame-background-underline; reverse: $dialog-frame-background-reverse }
CalculatorWindow:active        { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg; bold: $dialog-frame-background-bold; dim: $dialog-frame-background-dim; italic: $dialog-frame-background-italic; underline: $dialog-frame-background-underline; reverse: $dialog-frame-background-reverse }
CalculatorWindow::title,
CalculatorWindow:active::title { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg; bold: $dialog-frame-background-bold; dim: $dialog-frame-background-dim; italic: $dialog-frame-background-italic; underline: $dialog-frame-background-underline; reverse: $dialog-frame-background-reverse }
CalculatorWindow::icon         { fg: $dialog-frame-icons-fg; bg: $dialog-frame-icons-bg; bold: $dialog-frame-icons-bold; dim: $dialog-frame-icons-dim; italic: $dialog-frame-icons-italic; underline: $dialog-frame-icons-underline; reverse: $dialog-frame-icons-reverse }

/* A panel's own colours are its listing colours, which is also what the frame
   and the fill inherit -- as in the original, where the frame and the interior
   of a file panel share a background and differ only in intensity. */
Panel               { fg: $panel-fg; bg: $panel-bg; border: single; icons: auto; bold: $panel-bold; dim: $panel-dim; italic: $panel-italic; underline: $panel-underline; reverse: $panel-reverse }
Panel:focused       { border: double }

/* The path across the top frame. `TTopView.Draw' picks between these two on
   `sfSelected', which is this `:active'. */
Panel::title        { fg: $title-fg; bg: $title-bg; bold: $title-bold; dim: $title-dim; italic: $title-italic; underline: $title-underline; reverse: $title-reverse }
Panel:focused::title { fg: $active-title-fg; bg: $active-title-bg; bold: $active-title-bold; dim: $active-title-dim; italic: $active-title-italic; underline: $active-title-underline; reverse: $active-title-reverse }

/* These two tie on specificity -- a class and a state each -- so source order
   is what settles a directory under the cursor, and the cursor has to come
   second. Both name `fg' and `bg', so the winner takes the row outright; were
   either to mention a property the other left out, the per-property cascade
   would carry that one property across from the loser. */
Panel::row.directory { fg: $directory-fg; bg: $directory-bg; bold: $directory-bold; dim: $directory-dim; italic: $directory-italic; underline: $directory-underline; reverse: $directory-reverse }

/* What kind of file a row is (`navigator/filetypes.py'): DOS Navigator's
   categories by mask and Midnight Commander's classes by type, a row taking
   at most one and the type winning.  All tie with `.directory' and the two
   rules after them, so they sit between: a link to a directory is coloured a
   link (keeping `.directory''s bold), and the cursor and a tag still win.
   Executables [173] and Archives [174] are DN's own slots; the rest are
   Navigator's variables, each an alias of one of DN's Custom 1-5
   [175-181] -- see `DERIVED' in `tools/palconv.py'. */
Panel::row.executable { fg: $executable-fg; bg: $executable-bg; bold: $executable-bold; dim: $executable-dim; italic: $executable-italic; underline: $executable-underline; reverse: $executable-reverse }
Panel::row.archive    { fg: $archive-fg;    bg: $archive-bg; bold: $archive-bold; dim: $archive-dim; italic: $archive-italic; underline: $archive-underline; reverse: $archive-reverse }
Panel::row.image      { fg: $image-fg;      bg: $image-bg; bold: $image-bold; dim: $image-dim; italic: $image-italic; underline: $image-underline; reverse: $image-reverse }
Panel::row.media      { fg: $media-fg;      bg: $media-bg; bold: $media-bold; dim: $media-dim; italic: $media-italic; underline: $media-underline; reverse: $media-reverse }
Panel::row.document   { fg: $document-fg;   bg: $document-bg; bold: $document-bold; dim: $document-dim; italic: $document-italic; underline: $document-underline; reverse: $document-reverse }
Panel::row.source     { fg: $source-fg;     bg: $source-bg; bold: $source-bold; dim: $source-dim; italic: $source-italic; underline: $source-underline; reverse: $source-reverse }
Panel::row.temp       { fg: $temp-fg;       bg: $temp-bg; bold: $temp-bold; dim: $temp-dim; italic: $temp-italic; underline: $temp-underline; reverse: $temp-reverse }
Panel::row.symlink    { fg: $symlink-fg;    bg: $symlink-bg; bold: $symlink-bold; dim: $symlink-dim; italic: $symlink-italic; underline: $symlink-underline; reverse: $symlink-reverse }
Panel::row.stale-link { fg: $stale-link-fg; bg: $stale-link-bg; bold: $stale-link-bold; dim: $stale-link-dim; italic: $stale-link-italic; underline: $stale-link-underline; reverse: $stale-link-reverse }
Panel::row.device     { fg: $device-fg;     bg: $device-bg; bold: $device-bold; dim: $device-dim; italic: $device-italic; underline: $device-underline; reverse: $device-reverse }
Panel::row.special    { fg: $special-fg;    bg: $special-bg; bold: $special-bold; dim: $special-dim; italic: $special-italic; underline: $special-underline; reverse: $special-reverse }

Panel::row:selected  { fg: $cursor-fg; bg: $cursor-bg; bold: $cursor-bold; dim: $cursor-dim; italic: $cursor-italic; underline: $cursor-underline; reverse: $cursor-reverse }

/* A tagged entry (Insert): `[87] Selected text', and under the cursor `[89]
   Selected cursor' -- the C3 and C5 of `TFilePanel.Draw', which overrode the
   directory highlight as these override `.directory'. `bold: false' because
   `.directory' names it and the per-property cascade would otherwise carry
   it across. The cursor one wins on specificity, a class and a state. */
Panel::row.marked          { fg: $marked-fg; bg: $marked-bg; bold: $marked-bold; dim: $marked-dim; italic: $marked-italic; underline: $marked-underline; reverse: $marked-reverse }
Panel::row.marked:selected { fg: $marked-cursor-fg; bg: $marked-cursor-bg; bold: $marked-cursor-bold; dim: $marked-cursor-dim; italic: $marked-cursor-italic; underline: $marked-cursor-underline; reverse: $marked-cursor-reverse }

/* The detailed and list modes (Ctrl+Y): the column titles over them, `[165]
   Column title', and the rules between their columns in the frame's own
   colours, so a rule and the tees joining it to the frame read as one line.
   A departure: DN drew them in `[86] List divider', which is left inert. */
Panel::heading       { fg: $column-title-fg; bg: $column-title-bg; bold: $column-title-bold; dim: $column-title-dim; italic: $column-title-italic; underline: $column-title-underline; reverse: $column-title-reverse }
Panel::divider       { fg: $panel-fg; bg: $panel-bg; bold: $panel-bold; dim: $panel-dim; italic: $panel-italic; underline: $panel-underline; reverse: $panel-reverse }
/* The info lines under the listing (TInfoView): [122]-[125]. */
Panel::totals             { fg: $info-totals-text-fg; bg: $info-totals-text-bg; bold: $info-totals-text-bold; dim: $info-totals-text-dim; italic: $info-totals-text-italic; underline: $info-totals-text-underline; reverse: $info-totals-text-reverse }
Panel::totals-numbers     { fg: $info-totals-numbers-fg; bg: $info-totals-numbers-bg; bold: $info-totals-numbers-bold; dim: $info-totals-numbers-dim; italic: $info-totals-numbers-italic; underline: $info-totals-numbers-underline; reverse: $info-totals-numbers-reverse }
Panel::free-space         { fg: $info-free-space-text-fg; bg: $info-free-space-text-bg; bold: $info-free-space-text-bold; dim: $info-free-space-text-dim; italic: $info-free-space-text-italic; underline: $info-free-space-text-underline; reverse: $info-free-space-text-reverse }
Panel::free-space-numbers { fg: $info-free-space-numbers-fg; bg: $info-free-space-numbers-bg; bold: $info-free-space-numbers-bold; dim: $info-free-space-numbers-dim; italic: $info-free-space-numbers-italic; underline: $info-free-space-numbers-underline; reverse: $info-free-space-numbers-reverse }

/* The directory tree a panel becomes (Ctrl+T): the File Manager group's own
   tree slots, [94] to [101].  The lines and the ground are *Normal tree*, the
   names *Normal nodes*; the cursor is *Selected node* while the tree has the
   keyboard and *Selected passive* while it has not -- TTreeView.Draw's C3
   against C6 -- and the two rows under it are *Info box*.  Framed like a
   panel, since it stands where one stood. */
DirectoryTree                        { fg: $tree-normal-tree-fg; bg: $tree-normal-tree-bg; border: single; bold: $tree-normal-tree-bold; dim: $tree-normal-tree-dim; italic: $tree-normal-tree-italic; underline: $tree-normal-tree-underline; reverse: $tree-normal-tree-reverse }
DirectoryTree:focused                { border: double }
DirectoryTree::node                  { fg: $tree-normal-nodes-fg; bg: $tree-normal-nodes-bg; bold: $tree-normal-nodes-bold; dim: $tree-normal-nodes-dim; italic: $tree-normal-nodes-italic; underline: $tree-normal-nodes-underline; reverse: $tree-normal-nodes-reverse }
DirectoryTree::node:selected         { fg: $tree-selected-passive-fg; bg: $tree-selected-passive-bg; bold: $tree-selected-passive-bold; dim: $tree-selected-passive-dim; italic: $tree-selected-passive-italic; underline: $tree-selected-passive-underline; reverse: $tree-selected-passive-reverse }
DirectoryTree:focused::node:selected { fg: $tree-selected-node-fg; bg: $tree-selected-node-bg; bold: $tree-selected-node-bold; dim: $tree-selected-node-dim; italic: $tree-selected-node-italic; underline: $tree-selected-node-underline; reverse: $tree-selected-node-reverse }
DirectoryTree::info                  { fg: $tree-info-box-fg; bg: $tree-info-box-bg; bold: $tree-info-box-bold; dim: $tree-info-box-dim; italic: $tree-info-box-italic; underline: $tree-info-box-underline; reverse: $tree-info-box-reverse }

/* The quick view a panel becomes (Ctrl+Q): THFileViewer takes CHViewer,
   which is CDoubleWindow's 13 and 14 -- the File Manager group's *Quick View*
   text, [92] and [93].  Framed and titled like a panel, since it stands where
   one stood; its scroll bar is the panel's. */
InfoPanel                            { fg: $panel-fg; bg: $panel-bg; border: single; bold: $panel-bold; dim: $panel-dim; italic: $panel-italic; underline: $panel-underline; reverse: $panel-reverse }
InfoPanel:focused                    { border: double }
InfoPanel::title                     { fg: $title-fg; bg: $title-bg; bold: $title-bold; dim: $title-dim; italic: $title-italic; underline: $title-underline; reverse: $title-reverse }
InfoPanel::highlight                 { fg: $directory-fg; bg: $panel-bg; bold: $directory-bold; dim: $directory-dim; italic: $directory-italic; underline: $directory-underline; reverse: $directory-reverse }
QuickViewer                          { fg: $panel-fg; bg: $panel-bg; border: single; bold: $panel-bold; dim: $panel-dim; italic: $panel-italic; underline: $panel-underline; reverse: $panel-reverse }
QuickViewer:focus_within             { border: double }
QuickViewer::title                   { fg: $title-fg; bg: $title-bg; bold: $title-bold; dim: $title-dim; italic: $title-italic; underline: $title-underline; reverse: $title-reverse }
QuickViewer:focus_within::title      { fg: $active-title-fg; bg: $active-title-bg; bold: $active-title-bold; dim: $active-title-dim; italic: $active-title-italic; underline: $active-title-underline; reverse: $active-title-reverse }
QuickViewer FileViewer               { fg: $quick-view-normal-text-fg; bg: $quick-view-normal-text-bg; bold: $quick-view-normal-text-bold; dim: $quick-view-normal-text-dim; italic: $quick-view-normal-text-italic; underline: $quick-view-normal-text-underline; reverse: $quick-view-normal-text-reverse }
QuickViewer FileViewer::selected     { fg: $quick-view-selected-text-fg; bg: $quick-view-selected-text-bg; bold: $quick-view-selected-text-bold; dim: $quick-view-selected-text-dim; italic: $quick-view-selected-text-italic; underline: $quick-view-selected-text-underline; reverse: $quick-view-selected-text-reverse }

/* One palette entry, two bars: Turbo Vision gives `TMenuView' and
   `TStatusLine' the same six colours (MENUS.PAS), and DOS Navigator never
   split them. Hence `$bar-' rather than a name that claims otherwise. */
MenuBar, MenuBox                      { fg: $bar-fg; bg: $bar-bg; bold: $bar-bold; dim: $bar-dim; italic: $bar-italic; underline: $bar-underline; reverse: $bar-reverse }
MenuBar::hotkey, MenuBox::hotkey      { fg: $bar-key-fg; bg: $bar-key-bg; bold: $bar-key-bold; dim: $bar-key-dim; italic: $bar-key-italic; underline: $bar-key-underline; reverse: $bar-key-reverse }
MenuBar::item:selected,
MenuBox::item:selected                { fg: $bar-selected-fg; bg: $bar-selected-bg; bold: $bar-selected-bold; dim: $bar-selected-dim; italic: $bar-selected-italic; underline: $bar-selected-underline; reverse: $bar-selected-reverse }
MenuBar::hotkey:selected,
MenuBox::hotkey:selected              { fg: $bar-selected-key-fg; bg: $bar-selected-key-bg; bold: $bar-selected-key-bold; dim: $bar-selected-key-dim; italic: $bar-selected-key-italic; underline: $bar-selected-key-underline; reverse: $bar-selected-key-reverse }
/* A disabled entry is greyed whole, its marked letter included: Turbo
   Vision draws it with one colour pair, [3] or [6], for both halves. */
MenuBar::item:disabled, MenuBar::hotkey:disabled,
MenuBox::item:disabled, MenuBox::hotkey:disabled
                                      { fg: $bar-disabled-fg; bg: $bar-disabled-bg; bold: $bar-disabled-bold; dim: $bar-disabled-dim; italic: $bar-disabled-italic; underline: $bar-disabled-underline; reverse: $bar-disabled-reverse }
MenuBar::item:selected:disabled, MenuBar::hotkey:selected:disabled,
MenuBox::item:selected:disabled, MenuBox::hotkey:selected:disabled
                                      { fg: $bar-selected-disabled-fg; bg: $bar-selected-disabled-bg; bold: $bar-selected-disabled-bold; dim: $bar-selected-disabled-dim; italic: $bar-selected-disabled-italic; underline: $bar-selected-disabled-underline; reverse: $bar-selected-disabled-reverse }

/* DOS Navigator's Colors dialog names slot [1] "Timer": it is the clock's
   colour first, and the background (CBackground) shares it. */
Clock { fg: $desktop-fg; bg: $desktop-bg; bold: $desktop-bold; dim: $desktop-dim; italic: $desktop-italic; underline: $desktop-underline; reverse: $desktop-reverse }

KeyBar      { fg: $bar-fg; bg: $bar-bg; bold: $bar-bold; dim: $bar-dim; italic: $bar-italic; underline: $bar-underline; reverse: $bar-reverse }
KeyBar::key { fg: $bar-key-fg; bg: $bar-key-bg; bold: $bar-key-bold; dim: $bar-key-dim; italic: $bar-key-italic; underline: $bar-key-underline; reverse: $bar-key-reverse }
/* A command that cannot run: slot [3], "Disabled -- CMenuView, CStatusLine".
   Turbo Vision greys the whole item, its key included, so the key takes it
   too -- and wins over the rule above by being the more specific. */
KeyBar::label:disabled,
KeyBar::key:disabled { fg: $bar-disabled-fg; bg: $bar-disabled-bg; bold: $bar-disabled-bold; dim: $bar-disabled-dim; italic: $bar-disabled-italic; underline: $bar-disabled-underline; reverse: $bar-disabled-reverse }

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

Modal                 { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg; bold: $dialog-frame-background-bold; dim: $dialog-frame-background-dim; italic: $dialog-frame-background-italic; underline: $dialog-frame-background-underline; reverse: $dialog-frame-background-reverse }
Modal::title          { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg; bold: $dialog-frame-background-bold; dim: $dialog-frame-background-dim; italic: $dialog-frame-background-italic; underline: $dialog-frame-background-underline; reverse: $dialog-frame-background-reverse }
Modal::icon           { fg: $dialog-frame-icons-fg;      bg: $dialog-frame-icons-bg; bold: $dialog-frame-icons-bold; dim: $dialog-frame-icons-dim; italic: $dialog-frame-icons-italic; underline: $dialog-frame-icons-underline; reverse: $dialog-frame-icons-reverse }

StaticText            { fg: $dialog-static-text-fg;      bg: $dialog-static-text-bg; bold: $dialog-static-text-bold; dim: $dialog-static-text-dim; italic: $dialog-static-text-italic; underline: $dialog-static-text-underline; reverse: $dialog-static-text-reverse }
/* An ofFramed view's frame is drawn in the dialog's own colours, its caption a label's. */
GroupBox              { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg; border: single; bold: $dialog-frame-background-bold; dim: $dialog-frame-background-dim; italic: $dialog-frame-background-italic; underline: $dialog-frame-background-underline; reverse: $dialog-frame-background-reverse }
GroupBox::title       { fg: $dialog-label-normal-fg;     bg: $dialog-label-normal-bg; bold: $dialog-label-normal-bold; dim: $dialog-label-normal-dim; italic: $dialog-label-normal-italic; underline: $dialog-label-normal-underline; reverse: $dialog-label-normal-reverse }
GroupBox::shortcut    { fg: $dialog-label-shortcut-fg;   bg: $dialog-label-shortcut-bg; bold: $dialog-label-shortcut-bold; dim: $dialog-label-shortcut-dim; italic: $dialog-label-shortcut-italic; underline: $dialog-label-shortcut-underline; reverse: $dialog-label-shortcut-reverse }

/* A gauge in `TWhileView''s colour, which is its lines' colour: `GetColor(7)'
 * of `CDialog', and `CGrayDialog' maps entry 7 to [38] *Label normal*, not to
 * [37].  `█' is the foreground and `▒' the foreground's shade over the
 * background -- black and, to the eye, dark grey in DEFAULT.PAL.  Without a
 * rule the bar inherited the dialog frame's white. */
ProgressBar           { fg: $dialog-label-normal-fg;     bg: $dialog-label-normal-bg; bold: $dialog-label-normal-bold; dim: $dialog-label-normal-dim; italic: $dialog-label-normal-italic; underline: $dialog-label-normal-underline; reverse: $dialog-label-normal-reverse }
/* A spinner beside a box's message turns in the message's colour. */
Spinner               { fg: $dialog-static-text-fg;      bg: $dialog-static-text-bg; bold: $dialog-static-text-bold; dim: $dialog-static-text-dim; italic: $dialog-static-text-italic; underline: $dialog-static-text-underline; reverse: $dialog-static-text-reverse }

Label                 { fg: $dialog-label-normal-fg;     bg: $dialog-label-normal-bg; bold: $dialog-label-normal-bold; dim: $dialog-label-normal-dim; italic: $dialog-label-normal-italic; underline: $dialog-label-normal-underline; reverse: $dialog-label-normal-reverse }
Label:selected        { fg: $dialog-label-selected-fg;   bg: $dialog-label-selected-bg; bold: $dialog-label-selected-bold; dim: $dialog-label-selected-dim; italic: $dialog-label-selected-italic; underline: $dialog-label-selected-underline; reverse: $dialog-label-selected-reverse }
/* `bg' as well as `fg' on the two shortcut rules below, because `mono' gives
 * a shortcut a different background from an ordinary caption and the other
 * ten do not.  Naming only `fg' would read correctly in ten themes. */
Label::shortcut       { fg: $dialog-label-shortcut-fg;   bg: $dialog-label-shortcut-bg; bold: $dialog-label-shortcut-bold; dim: $dialog-label-shortcut-dim; italic: $dialog-label-shortcut-italic; underline: $dialog-label-shortcut-underline; reverse: $dialog-label-shortcut-reverse }

Button                { fg: $dialog-button-normal-fg;    bg: $dialog-button-normal-bg; bold: $dialog-button-normal-bold; dim: $dialog-button-normal-dim; italic: $dialog-button-normal-italic; underline: $dialog-button-normal-underline; reverse: $dialog-button-normal-reverse }
Button:am_default     { fg: $dialog-button-default-fg;   bg: $dialog-button-default-bg; bold: $dialog-button-default-bold; dim: $dialog-button-default-dim; italic: $dialog-button-default-italic; underline: $dialog-button-default-underline; reverse: $dialog-button-default-reverse }
Button:focused        { fg: $dialog-button-selected-fg;  bg: $dialog-button-selected-bg; bold: $dialog-button-selected-bold; dim: $dialog-button-selected-dim; italic: $dialog-button-selected-italic; underline: $dialog-button-selected-underline; reverse: $dialog-button-selected-reverse }
Button:inert          { fg: $dialog-button-disabled-fg;  bg: $dialog-button-disabled-bg; bold: $dialog-button-disabled-bold; dim: $dialog-button-disabled-dim; italic: $dialog-button-disabled-italic; underline: $dialog-button-disabled-underline; reverse: $dialog-button-disabled-reverse }
Button::shadow        { fg: $dialog-button-shadow-fg;    bg: $dialog-button-shadow-bg; bold: $dialog-button-shadow-bold; dim: $dialog-button-shadow-dim; italic: $dialog-button-shadow-italic; underline: $dialog-button-shadow-underline; reverse: $dialog-button-shadow-reverse }
/* The caption is a StaticText, and the StaticText rule above would give it
 * the dialog's static-text colours over the button's own, so it repeats the
 * button's four rules -- one more type in each selector, so these win. */
Button StaticText            { fg: $dialog-button-normal-fg;    bg: $dialog-button-normal-bg; bold: $dialog-button-normal-bold; dim: $dialog-button-normal-dim; italic: $dialog-button-normal-italic; underline: $dialog-button-normal-underline; reverse: $dialog-button-normal-reverse }
Button:am_default StaticText { fg: $dialog-button-default-fg;   bg: $dialog-button-default-bg; bold: $dialog-button-default-bold; dim: $dialog-button-default-dim; italic: $dialog-button-default-italic; underline: $dialog-button-default-underline; reverse: $dialog-button-default-reverse }
Button:focused StaticText    { fg: $dialog-button-selected-fg;  bg: $dialog-button-selected-bg; bold: $dialog-button-selected-bold; dim: $dialog-button-selected-dim; italic: $dialog-button-selected-italic; underline: $dialog-button-selected-underline; reverse: $dialog-button-selected-reverse }
Button:inert StaticText      { fg: $dialog-button-disabled-fg;  bg: $dialog-button-disabled-bg; bold: $dialog-button-disabled-bold; dim: $dialog-button-disabled-dim; italic: $dialog-button-disabled-italic; underline: $dialog-button-disabled-underline; reverse: $dialog-button-disabled-reverse }
/* The marked letter needs only its foreground: it takes its background from
 * whichever caption rule above won, which is the per-property cascade doing
 * exactly what it is for. */
Button StaticText::shortcut         { fg: $dialog-button-shortcut-fg; bold: $dialog-button-shortcut-bold; dim: $dialog-button-shortcut-dim; italic: $dialog-button-shortcut-italic; underline: $dialog-button-shortcut-underline; reverse: $dialog-button-shortcut-reverse }
Button:am_default StaticText::shortcut { fg: $dialog-shortcut-default-fg; bold: $dialog-shortcut-default-bold; dim: $dialog-shortcut-default-dim; italic: $dialog-shortcut-default-italic; underline: $dialog-shortcut-default-underline; reverse: $dialog-shortcut-default-reverse }
Button:focused StaticText::shortcut { fg: $dialog-shortcut-selected-fg; bold: $dialog-shortcut-selected-bold; dim: $dialog-shortcut-selected-dim; italic: $dialog-shortcut-selected-italic; underline: $dialog-shortcut-selected-underline; reverse: $dialog-shortcut-selected-reverse }

InputLine             { fg: $dialog-input-normal-fg;     bg: $dialog-input-normal-bg; bold: $dialog-input-normal-bold; dim: $dialog-input-normal-dim; italic: $dialog-input-normal-italic; underline: $dialog-input-normal-underline; reverse: $dialog-input-normal-reverse }
InputLine:focused     { fg: $dialog-input-selected-fg;   bg: $dialog-input-selected-bg; bold: $dialog-input-selected-bold; dim: $dialog-input-selected-dim; italic: $dialog-input-selected-italic; underline: $dialog-input-selected-underline; reverse: $dialog-input-selected-reverse }
InputLine::selection  { fg: $dialog-input-normal-fg;     bg: $dialog-input-selected-bg; bold: $dialog-input-normal-bold; dim: $dialog-input-normal-dim; italic: $dialog-input-normal-italic; underline: $dialog-input-normal-underline; reverse: $dialog-input-normal-reverse }
InputLine::arrow      { fg: $dialog-input-arrow-fg;      bg: $dialog-input-arrow-bg; bold: $dialog-input-arrow-bold; dim: $dialog-input-arrow-dim; italic: $dialog-input-arrow-italic; underline: $dialog-input-arrow-underline; reverse: $dialog-input-arrow-reverse }

/* A disabled control is greyed whole -- caption, marked letter, line, its
 * button and a cluster's items alike.  DOS Navigator's palette has no
 * disabled slot for any of them, only [44] Button disabled, so they all take
 * that one: in DN's own dialogs it is the dialog's grey with dark text, which
 * is what greyed out looks like on it.  A departure, since DN never disabled
 * a line; File Attributes' *User* is the one that needs it, for anyone but
 * root. */
Label:inert, Label:inert::shortcut,
InputLine:inert, InputLine:inert::arrow,
History:inert, History:inert::arrow,
Cluster:inert::item, Cluster:inert::mark, Cluster:inert::shortcut
                      { fg: $dialog-button-disabled-fg;  bg: $dialog-button-disabled-bg; bold: $dialog-button-disabled-bold; dim: $dialog-button-disabled-dim; italic: $dialog-button-disabled-italic; underline: $dialog-button-disabled-underline; reverse: $dialog-button-disabled-reverse }

/* The command line is the one rule here with colours in it rather than
   variables, because DOS Navigator had no slot for it either:
   `TCommandLine.Draw' writes the prompt in $0F and the text in $07, bright
   white and light grey on black, whatever the palette (CMDLINE.PAS).  Every
   theme is a transcription of a `.PAL', and a `.PAL' never carried these. */
CommandLine            { fg: light_gray; bg: black }
CommandLine::prompt    { fg: white }
CommandLine::selection { fg: black; bg: light_gray }

/* What a panel drag carries (drag.py): `TDragger.Draw' wrote $30, black on
   cyan, with no palette entry behind it -- so a literal here too. */
DragLabel              { fg: black; bg: cyan }

/* The screen savers (screen_saver.py): DN drew them in $07, light grey on
   black, its stars' bright ones in $0F -- no palette entry either. */
ScreenSaver            { fg: light_gray; bg: black }

/* The trash can (trash_can.py): DN's CGrayWindow, the gray dialogs' family --
   its text in their static text, dragged in their frame icons' colour. */
TrashCan               { fg: $dialog-static-text-fg; bg: $dialog-static-text-bg; bold: $dialog-static-text-bold; dim: $dialog-static-text-dim; italic: $dialog-static-text-italic; underline: $dialog-static-text-underline; reverse: $dialog-static-text-reverse }
TrashCan:dragging      { fg: $dialog-frame-icons-fg; bg: $dialog-frame-icons-bg; bold: $dialog-frame-icons-bold; dim: $dialog-frame-icons-dim; italic: $dialog-frame-icons-italic; underline: $dialog-frame-icons-underline; reverse: $dialog-frame-icons-reverse }
/* Interface's `Block Insert Cursor' (`ouiBlockInsertCursor'): on `Shell',
   which answers for the command line's caret.  Unticked, the terminal's own. */
Shell:block_insert { caret: block }
/* The history button, [53] and [54]; and the list it drops, which Turbo
   Vision's CHistoryWindow draws in the input line's own colours -- frame and
   rows [50], the selected row [51] -- with a scroll bar of its own, [55] and
   [56]. */
History                          { fg: $dialog-history-sides-fg;     bg: $dialog-history-sides-bg; bold: $dialog-history-sides-bold; dim: $dialog-history-sides-dim; italic: $dialog-history-sides-italic; underline: $dialog-history-sides-underline; reverse: $dialog-history-sides-reverse }
History::arrow                   { fg: $dialog-history-button-fg;    bg: $dialog-history-button-bg; bold: $dialog-history-button-bold; dim: $dialog-history-button-dim; italic: $dialog-history-button-italic; underline: $dialog-history-button-underline; reverse: $dialog-history-button-reverse }
HistoryList                      { fg: $dialog-input-normal-fg;      bg: $dialog-input-normal-bg; bold: $dialog-input-normal-bold; dim: $dialog-input-normal-dim; italic: $dialog-input-normal-italic; underline: $dialog-input-normal-underline; reverse: $dialog-input-normal-reverse }
HistoryList::row:selected        { fg: $dialog-input-selected-fg;    bg: $dialog-input-selected-bg; bold: $dialog-input-selected-bold; dim: $dialog-input-selected-dim; italic: $dialog-input-selected-italic; underline: $dialog-input-selected-underline; reverse: $dialog-input-selected-reverse }
HistoryList ScrollBar            { fg: $dialog-history-bar-page-fg;  bg: $dialog-history-bar-page-bg; bold: $dialog-history-bar-page-bold; dim: $dialog-history-bar-page-dim; italic: $dialog-history-bar-page-italic; underline: $dialog-history-bar-page-underline; reverse: $dialog-history-bar-page-reverse }
/* The calendar and the clock face a date or time line's button drops are its
   history list's kin, and take its colours: the line's own [50] for the frame
   and the days, [51] for the one under the cursor, and [52] Input arrow for
   what is not a value -- the month, its arrows, the weekdays, today.  No DN
   slot names them; neither existed. */
Calendar, TimePicker             { fg: $dialog-input-normal-fg;      bg: $dialog-input-normal-bg; bold: $dialog-input-normal-bold; dim: $dialog-input-normal-dim; italic: $dialog-input-normal-italic; underline: $dialog-input-normal-underline; reverse: $dialog-input-normal-reverse }
Calendar::title, Calendar::arrow,
Calendar::weekday, TimePicker::arrow,
TimePicker::separator            { fg: $dialog-input-arrow-fg;       bg: $dialog-input-arrow-bg; bold: $dialog-input-arrow-bold; dim: $dialog-input-arrow-dim; italic: $dialog-input-arrow-italic; underline: $dialog-input-arrow-underline; reverse: $dialog-input-arrow-reverse }
Calendar::day:today              { fg: $dialog-input-arrow-fg;       bg: $dialog-input-arrow-bg; bold: $dialog-input-arrow-bold; dim: $dialog-input-arrow-dim; italic: $dialog-input-arrow-italic; underline: $dialog-input-arrow-underline; reverse: $dialog-input-arrow-reverse }
Calendar::day:selected,
Calendar::title:selected,
TimePicker::value:selected       { fg: $dialog-input-selected-fg;    bg: $dialog-input-selected-bg; bold: $dialog-input-selected-bold; dim: $dialog-input-selected-dim; italic: $dialog-input-selected-italic; underline: $dialog-input-selected-underline; reverse: $dialog-input-selected-reverse }
HistoryList ScrollBar::arrow,
HistoryList ScrollBar::thumb     { fg: $dialog-history-bar-icons-fg; bg: $dialog-history-bar-icons-bg; bold: $dialog-history-bar-icons-bold; dim: $dialog-history-bar-icons-dim; italic: $dialog-history-bar-icons-italic; underline: $dialog-history-bar-icons-underline; reverse: $dialog-history-bar-icons-reverse }

CheckBoxes, RadioButtons     { fg: $dialog-cluster-normal-fg;   bg: $dialog-cluster-normal-bg; bold: $dialog-cluster-normal-bold; dim: $dialog-cluster-normal-dim; italic: $dialog-cluster-normal-italic; underline: $dialog-cluster-normal-underline; reverse: $dialog-cluster-normal-reverse }
CheckBoxes::item:selected,
RadioButtons::item:selected  { fg: $dialog-cluster-selected-fg; bg: $dialog-cluster-selected-bg; bold: $dialog-cluster-selected-bold; dim: $dialog-cluster-selected-dim; italic: $dialog-cluster-selected-italic; underline: $dialog-cluster-selected-underline; reverse: $dialog-cluster-selected-reverse }
CheckBoxes::shortcut,
RadioButtons::shortcut       { fg: $dialog-cluster-shortcut-fg; bg: $dialog-cluster-shortcut-bg; bold: $dialog-cluster-shortcut-bold; dim: $dialog-cluster-shortcut-dim; italic: $dialog-cluster-shortcut-italic; underline: $dialog-cluster-shortcut-underline; reverse: $dialog-cluster-shortcut-reverse }

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
ScrollBar                { fg: $scrollbar-page-fg;  bg: $scrollbar-page-bg; bold: $scrollbar-page-bold; dim: $scrollbar-page-dim; italic: $scrollbar-page-italic; underline: $scrollbar-page-underline; reverse: $scrollbar-page-reverse }
ScrollBar::arrow,
ScrollBar::thumb         { fg: $scrollbar-arrow-fg; bg: $scrollbar-arrow-bg; bold: $scrollbar-arrow-bold; dim: $scrollbar-arrow-dim; italic: $scrollbar-arrow-italic; underline: $scrollbar-arrow-underline; reverse: $scrollbar-arrow-reverse }

Modal ScrollBar          { fg: $dialog-scroll-bar-page-fg;  bg: $dialog-scroll-bar-page-bg; bold: $dialog-scroll-bar-page-bold; dim: $dialog-scroll-bar-page-dim; italic: $dialog-scroll-bar-page-italic; underline: $dialog-scroll-bar-page-underline; reverse: $dialog-scroll-bar-page-reverse }
Modal ScrollBar::arrow,
Modal ScrollBar::thumb   { fg: $dialog-scroll-bar-icons-fg; bg: $dialog-scroll-bar-icons-bg; bold: $dialog-scroll-bar-icons-bold; dim: $dialog-scroll-bar-icons-dim; italic: $dialog-scroll-bar-icons-italic; underline: $dialog-scroll-bar-icons-underline; reverse: $dialog-scroll-bar-icons-reverse }

Modal ListViewer             { fg: $dialog-list-normal-fg;     bg: $dialog-list-normal-bg; bold: $dialog-list-normal-bold; dim: $dialog-list-normal-dim; italic: $dialog-list-normal-italic; underline: $dialog-list-normal-underline; reverse: $dialog-list-normal-reverse }
Modal ListViewer::row:selected { fg: $dialog-list-focused-fg;  bg: $dialog-list-focused-bg; bold: $dialog-list-focused-bold; dim: $dialog-list-focused-dim; italic: $dialog-list-focused-italic; underline: $dialog-list-focused-underline; reverse: $dialog-list-focused-reverse }
Modal ListViewer::divider    { fg: $dialog-list-divider-fg;    bg: $dialog-list-divider-bg; bold: $dialog-list-divider-bold; dim: $dialog-list-divider-dim; italic: $dialog-list-divider-italic; underline: $dialog-list-divider-underline; reverse: $dialog-list-divider-reverse }
/* The Directory Tree window: TTreeWindow takes CTreeDialog, the dialog
   palette, so its frame is a dialog's and its tree the Dialogs group's Tree,
   [104] to [110], with the path and file count in the information pane [61].
   One class more specific than the panel tree's rules above, so it wins. */
TreeWindow                                     { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg; bold: $dialog-frame-background-bold; dim: $dialog-frame-background-dim; italic: $dialog-frame-background-italic; underline: $dialog-frame-background-underline; reverse: $dialog-frame-background-reverse }
TreeWindow:active                              { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg; bold: $dialog-frame-background-bold; dim: $dialog-frame-background-dim; italic: $dialog-frame-background-italic; underline: $dialog-frame-background-underline; reverse: $dialog-frame-background-reverse }
TreeWindow::title,
TreeWindow:active::title                       { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg; bold: $dialog-frame-background-bold; dim: $dialog-frame-background-dim; italic: $dialog-frame-background-italic; underline: $dialog-frame-background-underline; reverse: $dialog-frame-background-reverse }
TreeWindow::icon                               { fg: $dialog-frame-icons-fg;      bg: $dialog-frame-icons-bg; bold: $dialog-frame-icons-bold; dim: $dialog-frame-icons-dim; italic: $dialog-frame-icons-italic; underline: $dialog-frame-icons-underline; reverse: $dialog-frame-icons-reverse }
TreeWindow DirectoryTree                       { fg: $dialog-tree-normal-tree-fg;      bg: $dialog-tree-normal-tree-bg; bold: $dialog-tree-normal-tree-bold; dim: $dialog-tree-normal-tree-dim; italic: $dialog-tree-normal-tree-italic; underline: $dialog-tree-normal-tree-underline; reverse: $dialog-tree-normal-tree-reverse }
TreeWindow DirectoryTree::node                 { fg: $dialog-tree-normal-nodes-fg;     bg: $dialog-tree-normal-nodes-bg; bold: $dialog-tree-normal-nodes-bold; dim: $dialog-tree-normal-nodes-dim; italic: $dialog-tree-normal-nodes-italic; underline: $dialog-tree-normal-nodes-underline; reverse: $dialog-tree-normal-nodes-reverse }
TreeWindow DirectoryTree::node:selected        { fg: $dialog-tree-selected-passive-fg; bg: $dialog-tree-selected-passive-bg; bold: $dialog-tree-selected-passive-bold; dim: $dialog-tree-selected-passive-dim; italic: $dialog-tree-selected-passive-italic; underline: $dialog-tree-selected-passive-underline; reverse: $dialog-tree-selected-passive-reverse }
TreeWindow DirectoryTree:focused::node:selected { fg: $dialog-tree-selected-node-fg;   bg: $dialog-tree-selected-node-bg; bold: $dialog-tree-selected-node-bold; dim: $dialog-tree-selected-node-dim; italic: $dialog-tree-selected-node-italic; underline: $dialog-tree-selected-node-underline; reverse: $dialog-tree-selected-node-reverse }
TreeWindow DirectoryTree::info                 { fg: $dialog-information-pane-fg;  bg: $dialog-information-pane-bg; bold: $dialog-information-pane-bold; dim: $dialog-information-pane-dim; italic: $dialog-information-pane-italic; underline: $dialog-information-pane-underline; reverse: $dialog-information-pane-reverse }
TreeWindow ScrollBar                           { fg: $dialog-scroll-bar-page-fg;  bg: $dialog-scroll-bar-page-bg; bold: $dialog-scroll-bar-page-bold; dim: $dialog-scroll-bar-page-dim; italic: $dialog-scroll-bar-page-italic; underline: $dialog-scroll-bar-page-underline; reverse: $dialog-scroll-bar-page-reverse }
TreeWindow ScrollBar::arrow,
TreeWindow ScrollBar::thumb                    { fg: $dialog-scroll-bar-icons-fg; bg: $dialog-scroll-bar-icons-bg; bold: $dialog-scroll-bar-icons-bold; dim: $dialog-scroll-bar-icons-dim; italic: $dialog-scroll-bar-icons-italic; underline: $dialog-scroll-bar-icons-underline; reverse: $dialog-scroll-bar-icons-reverse }

/* The file viewer: TFileWindow takes CViewWindow, the File Viewer group
   [112] to [118] -- its frame, its scroll bar (TViewScroll, through
   CScrollBar), the text and a search hit.  TViewInfo draws over the bottom
   frame in GetColor(2), the active frame's colour. */
FileWindow                                     { fg: $viewer-frame-passive-fg; bg: $viewer-frame-passive-bg; bold: $viewer-frame-passive-bold; dim: $viewer-frame-passive-dim; italic: $viewer-frame-passive-italic; underline: $viewer-frame-passive-underline; reverse: $viewer-frame-passive-reverse }
FileWindow:active                              { fg: $viewer-frame-active-fg;  bg: $viewer-frame-active-bg; bold: $viewer-frame-active-bold; dim: $viewer-frame-active-dim; italic: $viewer-frame-active-italic; underline: $viewer-frame-active-underline; reverse: $viewer-frame-active-reverse }
FileWindow::title                              { fg: $viewer-frame-passive-fg; bg: $viewer-frame-passive-bg; bold: $viewer-frame-passive-bold; dim: $viewer-frame-passive-dim; italic: $viewer-frame-passive-italic; underline: $viewer-frame-passive-underline; reverse: $viewer-frame-passive-reverse }
FileWindow:active::title                       { fg: $viewer-frame-active-fg;  bg: $viewer-frame-active-bg; bold: $viewer-frame-active-bold; dim: $viewer-frame-active-dim; italic: $viewer-frame-active-italic; underline: $viewer-frame-active-underline; reverse: $viewer-frame-active-reverse }
FileWindow::icon                               { fg: $viewer-frame-icons-fg;   bg: $viewer-frame-icons-bg; bold: $viewer-frame-icons-bold; dim: $viewer-frame-icons-dim; italic: $viewer-frame-icons-italic; underline: $viewer-frame-icons-underline; reverse: $viewer-frame-icons-reverse }
FileWindow StaticText#info                     { fg: $viewer-frame-active-fg;  bg: $viewer-frame-active-bg; bold: $viewer-frame-active-bold; dim: $viewer-frame-active-dim; italic: $viewer-frame-active-italic; underline: $viewer-frame-active-underline; reverse: $viewer-frame-active-reverse }
FileWindow ScrollBar                           { fg: $viewer-scroll-bar-page-fg;  bg: $viewer-scroll-bar-page-bg; bold: $viewer-scroll-bar-page-bold; dim: $viewer-scroll-bar-page-dim; italic: $viewer-scroll-bar-page-italic; underline: $viewer-scroll-bar-page-underline; reverse: $viewer-scroll-bar-page-reverse }
FileWindow ScrollBar::arrow,
FileWindow ScrollBar::thumb                    { fg: $viewer-scroll-bar-icons-fg; bg: $viewer-scroll-bar-icons-bg; bold: $viewer-scroll-bar-icons-bold; dim: $viewer-scroll-bar-icons-dim; italic: $viewer-scroll-bar-icons-italic; underline: $viewer-scroll-bar-icons-underline; reverse: $viewer-scroll-bar-icons-reverse }
FileViewer                                     { fg: $viewer-normal-text-fg;   bg: $viewer-normal-text-bg; bold: $viewer-normal-text-bold; dim: $viewer-normal-text-dim; italic: $viewer-normal-text-italic; underline: $viewer-normal-text-underline; reverse: $viewer-normal-text-reverse }
FileViewer::selected                           { fg: $viewer-selected-text-fg; bg: $viewer-selected-text-bg; bold: $viewer-selected-text-bold; dim: $viewer-selected-text-dim; italic: $viewer-selected-text-italic; underline: $viewer-selected-text-underline; reverse: $viewer-selected-text-reverse }

/* The editor: TEditWindow takes CUniWindow, the Editor/Spreadsheet group
   [70] to [77] -- TEditFrame's frame, icons and title, TEditScrollBar's page
   and icons, the text and a block.  TInfoLine draws over the bottom frame in
   GetColor(8), the active frame's colour.  The caret is DN's NormalCursor
   while inserting and its BlockCursor while overwriting. */
EditWindow                                     { fg: $editor-frame-passive-fg; bg: $editor-frame-passive-bg; bold: $editor-frame-passive-bold; dim: $editor-frame-passive-dim; italic: $editor-frame-passive-italic; underline: $editor-frame-passive-underline; reverse: $editor-frame-passive-reverse }
EditWindow:active                              { fg: $editor-frame-active-fg;  bg: $editor-frame-active-bg; bold: $editor-frame-active-bold; dim: $editor-frame-active-dim; italic: $editor-frame-active-italic; underline: $editor-frame-active-underline; reverse: $editor-frame-active-reverse }
EditWindow::title                              { fg: $editor-frame-passive-fg; bg: $editor-frame-passive-bg; bold: $editor-frame-passive-bold; dim: $editor-frame-passive-dim; italic: $editor-frame-passive-italic; underline: $editor-frame-passive-underline; reverse: $editor-frame-passive-reverse }
EditWindow:active::title                       { fg: $editor-frame-title-fg;   bg: $editor-frame-title-bg; bold: $editor-frame-title-bold; dim: $editor-frame-title-dim; italic: $editor-frame-title-italic; underline: $editor-frame-title-underline; reverse: $editor-frame-title-reverse }
EditWindow::icon                               { fg: $editor-frame-icons-fg;   bg: $editor-frame-icons-bg; bold: $editor-frame-icons-bold; dim: $editor-frame-icons-dim; italic: $editor-frame-icons-italic; underline: $editor-frame-icons-underline; reverse: $editor-frame-icons-reverse }
EditWindow StaticText#info                     { fg: $editor-frame-active-fg;  bg: $editor-frame-active-bg; bold: $editor-frame-active-bold; dim: $editor-frame-active-dim; italic: $editor-frame-active-italic; underline: $editor-frame-active-underline; reverse: $editor-frame-active-reverse }
EditWindow ScrollBar                           { fg: $editor-scroll-bar-page-fg;  bg: $editor-scroll-bar-page-bg; bold: $editor-scroll-bar-page-bold; dim: $editor-scroll-bar-page-dim; italic: $editor-scroll-bar-page-italic; underline: $editor-scroll-bar-page-underline; reverse: $editor-scroll-bar-page-reverse }
EditWindow ScrollBar::arrow,
EditWindow ScrollBar::thumb                    { fg: $editor-scroll-bar-icons-fg; bg: $editor-scroll-bar-icons-bg; bold: $editor-scroll-bar-icons-bold; dim: $editor-scroll-bar-icons-dim; italic: $editor-scroll-bar-icons-italic; underline: $editor-scroll-bar-icons-underline; reverse: $editor-scroll-bar-icons-reverse }
FileEditor                                     { fg: $editor-normal-text-fg;   bg: $editor-normal-text-bg; caret: underline; bold: $editor-normal-text-bold; dim: $editor-normal-text-dim; italic: $editor-normal-text-italic; underline: $editor-normal-text-underline; reverse: $editor-normal-text-reverse }
FileEditor:overwrite                           { caret: block }
FileEditor::selected                           { fg: $editor-selected-text-fg; bg: $editor-selected-text-bg; bold: $editor-selected-text-bold; dim: $editor-selected-text-dim; italic: $editor-selected-text-italic; underline: $editor-selected-text-underline; reverse: $editor-selected-text-reverse }
/* HiliteLine and HiliteColumn: the Editor group's [182], [183] and [185]. */
FileEditor::current_line                       { fg: $editor-highlight-current-line-fg;          bg: $editor-highlight-current-line-bg; bold: $editor-highlight-current-line-bold; dim: $editor-highlight-current-line-dim; italic: $editor-highlight-current-line-italic; underline: $editor-highlight-current-line-underline; reverse: $editor-highlight-current-line-reverse }
FileEditor::current_line_selected              { fg: $editor-highlight-current-line-selected-fg; bg: $editor-highlight-current-line-selected-bg; bold: $editor-highlight-current-line-selected-bold; dim: $editor-highlight-current-line-selected-dim; italic: $editor-highlight-current-line-selected-italic; underline: $editor-highlight-current-line-selected-underline; reverse: $editor-highlight-current-line-selected-reverse }
FileEditor::current_column                     { fg: $editor-highlight-current-column-fg;        bg: $editor-highlight-current-column-bg; bold: $editor-highlight-current-column-bold; dim: $editor-highlight-current-column-dim; italic: $editor-highlight-current-column-italic; underline: $editor-highlight-current-column-underline; reverse: $editor-highlight-current-column-reverse }

/* A tree in a dialog: the Dialogs group's Tree, [104] to [110].  The path
   line under it (TDTreeInfoView in Choose Directory) is the Information
   pane, [61]. */
Modal StaticText#info                 { fg: $dialog-information-pane-fg;  bg: $dialog-information-pane-bg; bold: $dialog-information-pane-bold; dim: $dialog-information-pane-dim; italic: $dialog-information-pane-italic; underline: $dialog-information-pane-underline; reverse: $dialog-information-pane-reverse }
/* TFileInfoPane, CInfoPane: the file dialog's path and focused entry, the
   same Information pane, [61]. */
FileInfoPane                          { fg: $dialog-information-pane-fg;  bg: $dialog-information-pane-bg; bold: $dialog-information-pane-bold; dim: $dialog-information-pane-dim; italic: $dialog-information-pane-italic; underline: $dialog-information-pane-underline; reverse: $dialog-information-pane-reverse }
/* TTable in *ASCII Chart*: the dialog's text, and TTable.BlockCursor's caret. */
CharTable                             { fg: $dialog-static-text-fg;       bg: $dialog-static-text-bg; caret: block; bold: $dialog-static-text-bold; dim: $dialog-static-text-dim; italic: $dialog-static-text-italic; underline: $dialog-static-text-underline; reverse: $dialog-static-text-reverse }
Modal TreeView                        { fg: $dialog-tree-normal-tree-fg;      bg: $dialog-tree-normal-tree-bg; bold: $dialog-tree-normal-tree-bold; dim: $dialog-tree-normal-tree-dim; italic: $dialog-tree-normal-tree-italic; underline: $dialog-tree-normal-tree-underline; reverse: $dialog-tree-normal-tree-reverse }
Modal TreeView::node                  { fg: $dialog-tree-normal-nodes-fg;     bg: $dialog-tree-normal-nodes-bg; bold: $dialog-tree-normal-nodes-bold; dim: $dialog-tree-normal-nodes-dim; italic: $dialog-tree-normal-nodes-italic; underline: $dialog-tree-normal-nodes-underline; reverse: $dialog-tree-normal-nodes-reverse }
Modal TreeView::node:selected         { fg: $dialog-tree-selected-passive-fg; bg: $dialog-tree-selected-passive-bg; bold: $dialog-tree-selected-passive-bold; dim: $dialog-tree-selected-passive-dim; italic: $dialog-tree-selected-passive-italic; underline: $dialog-tree-selected-passive-underline; reverse: $dialog-tree-selected-passive-reverse }
Modal TreeView:focused::node:selected { fg: $dialog-tree-selected-node-fg;    bg: $dialog-tree-selected-node-bg; bold: $dialog-tree-selected-node-bold; dim: $dialog-tree-selected-node-dim; italic: $dialog-tree-selected-node-italic; underline: $dialog-tree-selected-node-underline; reverse: $dialog-tree-selected-node-reverse }

/* Running as root: `Shell' carries `.root', and every window and dialog title
   under it goes white on dark red, so a root session cannot be mistaken for
   another.  DOS had no root and DN no slot for it, so `$root-title' is one of
   palconv's DERIVED variables carrying a colour of its own.
   Last in the sheet on purpose: `.root Window::title' ties `FileWindow:active
   ::title' and its kin on specificity, and source order breaks the tie.  The
   active panel's title goes the same way, and so does Quick View's while it
   holds the keyboard; a passive one keeps the theme's. */
.root Window::title,
.root Modal::title,
.root Panel:focused::title,
.root QuickViewer:focus_within::title          { fg: $root-title-fg; bg: $root-title-bg; bold: $root-title-bold; dim: $root-title-dim; italic: $root-title-italic; underline: $root-title-underline; reverse: $root-title-reverse }
