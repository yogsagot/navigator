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

Shell { fg: $desktop-fg; bg: $desktop-bg }

/* A window on the desktop takes the File Manager's frame slots [80-82]: the
   one window that exists is the file manager, and the frame colours are what
   DOS Navigator's CDoubleWindow palette gives it.  The active window is drawn
   double, as a focused panel is. */
Window              { fg: $frame-fg; bg: $frame-bg; border: single }
Window:active       { fg: $active-frame-fg; bg: $active-frame-bg; border: double }
Window::title       { fg: $frame-fg; bg: $frame-bg }
Window:active::title { fg: $active-frame-fg; bg: $active-frame-bg }
Window::icon        { fg: $frame-icon-fg; bg: $frame-icon-bg }

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

/* What kind of file a row is (`navigator/filetypes.py'): DOS Navigator's
   categories by mask and Midnight Commander's classes by type, a row taking
   at most one and the type winning.  All tie with `.directory' and the two
   rules after them, so they sit between: a link to a directory is coloured a
   link (keeping `.directory''s bold), and the cursor and a tag still win.
   Executables [173] and Archives [174] are DN's own slots; the rest are
   Navigator's variables, each an alias of one of DN's Custom 1-5
   [175-181] -- see `DERIVED' in `tools/palconv.py'. */
Panel::row.executable { fg: $executable-fg; bg: $executable-bg }
Panel::row.archive    { fg: $archive-fg;    bg: $archive-bg }
Panel::row.image      { fg: $image-fg;      bg: $image-bg }
Panel::row.media      { fg: $media-fg;      bg: $media-bg }
Panel::row.document   { fg: $document-fg;   bg: $document-bg }
Panel::row.source     { fg: $source-fg;     bg: $source-bg }
Panel::row.temp       { fg: $temp-fg;       bg: $temp-bg }
Panel::row.symlink    { fg: $symlink-fg;    bg: $symlink-bg }
Panel::row.stale-link { fg: $stale-link-fg; bg: $stale-link-bg }
Panel::row.device     { fg: $device-fg;     bg: $device-bg }
Panel::row.special    { fg: $special-fg;    bg: $special-bg }

Panel::row:selected  { fg: $cursor-fg; bg: $cursor-bg }

/* A tagged entry (Insert): `[87] Selected text', and under the cursor `[89]
   Selected cursor' -- the C3 and C5 of `TFilePanel.Draw', which overrode the
   directory highlight as these override `.directory'. `bold: false' because
   `.directory' names it and the per-property cascade would otherwise carry
   it across. The cursor one wins on specificity, a class and a state. */
Panel::row.marked          { fg: $marked-fg; bg: $marked-bg; bold: false }
Panel::row.marked:selected { fg: $marked-cursor-fg; bg: $marked-cursor-bg; bold: false }

/* The detailed and list modes (Ctrl+Y): the column titles over them, `[165]
   Column title', and the rules between their columns in the frame's own
   colours, so a rule and the tees joining it to the frame read as one line.
   A departure: DN drew them in `[86] List divider', which is left inert. */
Panel::heading       { fg: $column-title-fg; bg: $column-title-bg }
Panel::divider       { fg: $panel-fg; bg: $panel-bg }

/* The directory tree a panel becomes (Ctrl+T): the File Manager group's own
   tree slots, [94] to [101].  The lines and the ground are *Normal tree*, the
   names *Normal nodes*; the cursor is *Selected node* while the tree has the
   keyboard and *Selected passive* while it has not -- TTreeView.Draw's C3
   against C6 -- and the two rows under it are *Info box*.  Framed like a
   panel, since it stands where one stood. */
DirectoryTree                        { fg: $tree-normal-tree-fg; bg: $tree-normal-tree-bg; border: single }
DirectoryTree:focused                { border: double }
DirectoryTree::node                  { fg: $tree-normal-nodes-fg; bg: $tree-normal-nodes-bg }
DirectoryTree::node:selected         { fg: $tree-selected-passive-fg; bg: $tree-selected-passive-bg }
DirectoryTree:focused::node:selected { fg: $tree-selected-node-fg; bg: $tree-selected-node-bg }
DirectoryTree::info                  { fg: $tree-info-box-fg; bg: $tree-info-box-bg }

/* The quick view a panel becomes (Ctrl+Q): THFileViewer takes CHViewer,
   which is CDoubleWindow's 13 and 14 -- the File Manager group's *Quick View*
   text, [92] and [93].  Framed and titled like a panel, since it stands where
   one stood; its scroll bar is the panel's. */
QuickViewer                          { fg: $panel-fg; bg: $panel-bg; border: single }
QuickViewer:focus_within             { border: double }
QuickViewer::title                   { fg: $title-fg; bg: $title-bg }
QuickViewer:focus_within::title      { fg: $active-title-fg; bg: $active-title-bg }
QuickViewer FileViewer               { fg: $quick-view-normal-text-fg; bg: $quick-view-normal-text-bg }
QuickViewer FileViewer::selected     { fg: $quick-view-selected-text-fg; bg: $quick-view-selected-text-bg }

/* One palette entry, two bars: Turbo Vision gives `TMenuView' and
   `TStatusLine' the same six colours (MENUS.PAS), and DOS Navigator never
   split them. Hence `$bar-' rather than a name that claims otherwise. */
MenuBar, MenuBox                      { fg: $bar-fg; bg: $bar-bg }
MenuBar::hotkey, MenuBox::hotkey      { fg: $bar-key-fg; bg: $bar-key-bg }
MenuBar::item:selected,
MenuBox::item:selected                { fg: $bar-selected-fg; bg: $bar-selected-bg }
MenuBar::hotkey:selected,
MenuBox::hotkey:selected              { fg: $bar-selected-key-fg; bg: $bar-selected-key-bg }
/* A disabled entry is greyed whole, its marked letter included: Turbo
   Vision draws it with one colour pair, [3] or [6], for both halves. */
MenuBar::item:disabled, MenuBar::hotkey:disabled,
MenuBox::item:disabled, MenuBox::hotkey:disabled
                                      { fg: $bar-disabled-fg; bg: $bar-disabled-bg }
MenuBar::item:selected:disabled, MenuBar::hotkey:selected:disabled,
MenuBox::item:selected:disabled, MenuBox::hotkey:selected:disabled
                                      { fg: $bar-selected-disabled-fg; bg: $bar-selected-disabled-bg }

/* DOS Navigator's Colors dialog names slot [1] "Timer": it is the clock's
   colour first, and the background (CBackground) shares it. */
Clock { fg: $desktop-fg; bg: $desktop-bg }

KeyBar      { fg: $bar-fg; bg: $bar-bg }
KeyBar::key { fg: $bar-key-fg; bg: $bar-key-bg }
/* A command that cannot run: slot [3], "Disabled -- CMenuView, CStatusLine".
   Turbo Vision greys the whole item, its key included, so the key takes it
   too -- and wins over the rule above by being the more specific. */
KeyBar::label:disabled,
KeyBar::key:disabled { fg: $bar-disabled-fg; bg: $bar-disabled-bg }

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

Modal                 { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg }
Modal::title          { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg }
Modal::icon           { fg: $dialog-frame-icons-fg;      bg: $dialog-frame-icons-bg }

StaticText            { fg: $dialog-static-text-fg;      bg: $dialog-static-text-bg }

/* A gauge in `TWhileView''s colour, which is its lines' colour: `GetColor(7)'
 * of `CDialog', and `CGrayDialog' maps entry 7 to [38] *Label normal*, not to
 * [37].  `█' is the foreground and `▒' the foreground's shade over the
 * background -- black and, to the eye, dark grey in DEFAULT.PAL.  Without a
 * rule the bar inherited the dialog frame's white. */
ProgressBar           { fg: $dialog-label-normal-fg;     bg: $dialog-label-normal-bg }

Label                 { fg: $dialog-label-normal-fg;     bg: $dialog-label-normal-bg }
Label:selected        { fg: $dialog-label-selected-fg;   bg: $dialog-label-selected-bg }
/* `bg' as well as `fg' on the two shortcut rules below, because `mono' gives
 * a shortcut a different background from an ordinary caption and the other
 * ten do not.  Naming only `fg' would read correctly in ten themes. */
Label::shortcut       { fg: $dialog-label-shortcut-fg;   bg: $dialog-label-shortcut-bg }

Button                { fg: $dialog-button-normal-fg;    bg: $dialog-button-normal-bg }
Button:am_default     { fg: $dialog-button-default-fg;   bg: $dialog-button-default-bg }
Button:focused        { fg: $dialog-button-selected-fg;  bg: $dialog-button-selected-bg }
Button:inert          { fg: $dialog-button-disabled-fg;  bg: $dialog-button-disabled-bg }
Button::shadow        { fg: $dialog-button-shadow-fg;    bg: $dialog-button-shadow-bg }
/* The caption is a StaticText, and the StaticText rule above would give it
 * the dialog's static-text colours over the button's own, so it repeats the
 * button's four rules -- one more type in each selector, so these win. */
Button StaticText            { fg: $dialog-button-normal-fg;    bg: $dialog-button-normal-bg }
Button:am_default StaticText { fg: $dialog-button-default-fg;   bg: $dialog-button-default-bg }
Button:focused StaticText    { fg: $dialog-button-selected-fg;  bg: $dialog-button-selected-bg }
Button:inert StaticText      { fg: $dialog-button-disabled-fg;  bg: $dialog-button-disabled-bg }
/* The marked letter needs only its foreground: it takes its background from
 * whichever caption rule above won, which is the per-property cascade doing
 * exactly what it is for. */
Button StaticText::shortcut         { fg: $dialog-button-shortcut-fg }
Button:am_default StaticText::shortcut { fg: $dialog-shortcut-default-fg }
Button:focused StaticText::shortcut { fg: $dialog-shortcut-selected-fg }

InputLine             { fg: $dialog-input-normal-fg;     bg: $dialog-input-normal-bg }
InputLine:focused     { fg: $dialog-input-selected-fg;   bg: $dialog-input-selected-bg }
InputLine::selection  { fg: $dialog-input-normal-fg;     bg: $dialog-input-selected-bg }
InputLine::arrow      { fg: $dialog-input-arrow-fg;      bg: $dialog-input-arrow-bg }

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
                      { fg: $dialog-button-disabled-fg;  bg: $dialog-button-disabled-bg }

/* The command line is the one rule here with colours in it rather than
   variables, because DOS Navigator had no slot for it either:
   `TCommandLine.Draw' writes the prompt in $0F and the text in $07, bright
   white and light grey on black, whatever the palette (CMDLINE.PAS).  Every
   theme is a transcription of a `.PAL', and a `.PAL' never carried these. */
CommandLine            { fg: light_gray; bg: black }
CommandLine::prompt    { fg: white }
CommandLine::selection { fg: black; bg: light_gray }
/* The history button, [53] and [54]; and the list it drops, which Turbo
   Vision's CHistoryWindow draws in the input line's own colours -- frame and
   rows [50], the selected row [51] -- with a scroll bar of its own, [55] and
   [56]. */
History                          { fg: $dialog-history-sides-fg;     bg: $dialog-history-sides-bg }
History::arrow                   { fg: $dialog-history-button-fg;    bg: $dialog-history-button-bg }
HistoryList                      { fg: $dialog-input-normal-fg;      bg: $dialog-input-normal-bg }
HistoryList::row:selected        { fg: $dialog-input-selected-fg;    bg: $dialog-input-selected-bg }
HistoryList ScrollBar            { fg: $dialog-history-bar-page-fg;  bg: $dialog-history-bar-page-bg }
/* The calendar and the clock face a date or time line's button drops are its
   history list's kin, and take its colours: the line's own [50] for the frame
   and the days, [51] for the one under the cursor, and [52] Input arrow for
   what is not a value -- the month, its arrows, the weekdays, today.  No DN
   slot names them; neither existed. */
Calendar, TimePicker             { fg: $dialog-input-normal-fg;      bg: $dialog-input-normal-bg }
Calendar::title, Calendar::arrow,
Calendar::weekday, TimePicker::arrow,
TimePicker::separator            { fg: $dialog-input-arrow-fg;       bg: $dialog-input-arrow-bg }
Calendar::day:today              { fg: $dialog-input-arrow-fg;       bg: $dialog-input-arrow-bg }
Calendar::day:selected,
Calendar::title:selected,
TimePicker::value:selected       { fg: $dialog-input-selected-fg;    bg: $dialog-input-selected-bg }
HistoryList ScrollBar::arrow,
HistoryList ScrollBar::thumb     { fg: $dialog-history-bar-icons-fg; bg: $dialog-history-bar-icons-bg }

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

Modal ScrollBar          { fg: $dialog-scroll-bar-page-fg;  bg: $dialog-scroll-bar-page-bg }
Modal ScrollBar::arrow,
Modal ScrollBar::thumb   { fg: $dialog-scroll-bar-icons-fg; bg: $dialog-scroll-bar-icons-bg }

Modal ListViewer             { fg: $dialog-list-normal-fg;     bg: $dialog-list-normal-bg }
Modal ListViewer::row:selected { fg: $dialog-list-focused-fg;  bg: $dialog-list-focused-bg }
Modal ListViewer::divider    { fg: $dialog-list-divider-fg;    bg: $dialog-list-divider-bg }
/* The Directory Tree window: TTreeWindow takes CTreeDialog, the dialog
   palette, so its frame is a dialog's and its tree the Dialogs group's Tree,
   [104] to [110], with the path and file count in the information pane [61].
   One class more specific than the panel tree's rules above, so it wins. */
TreeWindow                                     { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg }
TreeWindow:active                              { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg }
TreeWindow::title,
TreeWindow:active::title                       { fg: $dialog-frame-background-fg; bg: $dialog-frame-background-bg }
TreeWindow::icon                               { fg: $dialog-frame-icons-fg;      bg: $dialog-frame-icons-bg }
TreeWindow DirectoryTree                       { fg: $dialog-tree-normal-tree-fg;      bg: $dialog-tree-normal-tree-bg }
TreeWindow DirectoryTree::node                 { fg: $dialog-tree-normal-nodes-fg;     bg: $dialog-tree-normal-nodes-bg }
TreeWindow DirectoryTree::node:selected        { fg: $dialog-tree-selected-passive-fg; bg: $dialog-tree-selected-passive-bg }
TreeWindow DirectoryTree:focused::node:selected { fg: $dialog-tree-selected-node-fg;   bg: $dialog-tree-selected-node-bg }
TreeWindow DirectoryTree::info                 { fg: $dialog-information-pane-fg;  bg: $dialog-information-pane-bg }
TreeWindow ScrollBar                           { fg: $dialog-scroll-bar-page-fg;  bg: $dialog-scroll-bar-page-bg }
TreeWindow ScrollBar::arrow,
TreeWindow ScrollBar::thumb                    { fg: $dialog-scroll-bar-icons-fg; bg: $dialog-scroll-bar-icons-bg }

/* The file viewer: TFileWindow takes CViewWindow, the File Viewer group
   [112] to [118] -- its frame, its scroll bar (TViewScroll, through
   CScrollBar), the text and a search hit.  TViewInfo draws over the bottom
   frame in GetColor(2), the active frame's colour. */
FileWindow                                     { fg: $viewer-frame-passive-fg; bg: $viewer-frame-passive-bg }
FileWindow:active                              { fg: $viewer-frame-active-fg;  bg: $viewer-frame-active-bg }
FileWindow::title                              { fg: $viewer-frame-passive-fg; bg: $viewer-frame-passive-bg }
FileWindow:active::title                       { fg: $viewer-frame-active-fg;  bg: $viewer-frame-active-bg }
FileWindow::icon                               { fg: $viewer-frame-icons-fg;   bg: $viewer-frame-icons-bg }
FileWindow StaticText#info                     { fg: $viewer-frame-active-fg;  bg: $viewer-frame-active-bg }
FileWindow ScrollBar                           { fg: $viewer-scroll-bar-page-fg;  bg: $viewer-scroll-bar-page-bg }
FileWindow ScrollBar::arrow,
FileWindow ScrollBar::thumb                    { fg: $viewer-scroll-bar-icons-fg; bg: $viewer-scroll-bar-icons-bg }
FileViewer                                     { fg: $viewer-normal-text-fg;   bg: $viewer-normal-text-bg }
FileViewer::selected                           { fg: $viewer-selected-text-fg; bg: $viewer-selected-text-bg }

/* The editor: TEditWindow takes CUniWindow, the Editor/Spreadsheet group
   [70] to [77] -- TEditFrame's frame, icons and title, TEditScrollBar's page
   and icons, the text and a block.  TInfoLine draws over the bottom frame in
   GetColor(8), the active frame's colour.  The caret is DN's NormalCursor
   while inserting and its BlockCursor while overwriting. */
EditWindow                                     { fg: $editor-frame-passive-fg; bg: $editor-frame-passive-bg }
EditWindow:active                              { fg: $editor-frame-active-fg;  bg: $editor-frame-active-bg }
EditWindow::title                              { fg: $editor-frame-passive-fg; bg: $editor-frame-passive-bg }
EditWindow:active::title                       { fg: $editor-frame-title-fg;   bg: $editor-frame-title-bg }
EditWindow::icon                               { fg: $editor-frame-icons-fg;   bg: $editor-frame-icons-bg }
EditWindow StaticText#info                     { fg: $editor-frame-active-fg;  bg: $editor-frame-active-bg }
EditWindow ScrollBar                           { fg: $editor-scroll-bar-page-fg;  bg: $editor-scroll-bar-page-bg }
EditWindow ScrollBar::arrow,
EditWindow ScrollBar::thumb                    { fg: $editor-scroll-bar-icons-fg; bg: $editor-scroll-bar-icons-bg }
FileEditor                                     { fg: $editor-normal-text-fg;   bg: $editor-normal-text-bg; caret: underline }
FileEditor:overwrite                           { caret: block }
FileEditor::selected                           { fg: $editor-selected-text-fg; bg: $editor-selected-text-bg }

/* A tree in a dialog: the Dialogs group's Tree, [104] to [110].  The path
   line under it (TDTreeInfoView in Choose Directory) is the Information
   pane, [61]. */
Modal StaticText#info                 { fg: $dialog-information-pane-fg;  bg: $dialog-information-pane-bg }
Modal TreeView                        { fg: $dialog-tree-normal-tree-fg;      bg: $dialog-tree-normal-tree-bg }
Modal TreeView::node                  { fg: $dialog-tree-normal-nodes-fg;     bg: $dialog-tree-normal-nodes-bg }
Modal TreeView::node:selected         { fg: $dialog-tree-selected-passive-fg; bg: $dialog-tree-selected-passive-bg }
Modal TreeView:focused::node:selected { fg: $dialog-tree-selected-node-fg;    bg: $dialog-tree-selected-node-bg }

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
.root QuickViewer:focus_within::title          { fg: $root-title-fg; bg: $root-title-bg }
