## Trees

`navml/widgets/dialog/tree_view/` is DOS Navigator's `TTreeView` (`TREE.PAS`), and Navigator's
`navigator/widgets/tree/directory_tree/` is its `THTreeView`, the tree a panel becomes.

**The rows are a flat list**, as DOS Navigator's `DC` collection is: the visible nodes, depth first, each knowing its
level. So `TreeView` is a `ListViewer` whose items are those rows, re-flattened whenever a branch opens or closes,
and it inherits the frame, the scroll bar on it, the cursor, the wheel and the clicks. A node is data, never a
widget, which is the recorded rule for listings. The node model is not reactive, so `revision` is one counter
standing for all of it, as `Console.revision` stands for a screen.

**Nodes load lazily.** A `TreeNode` carries its children or a *loader* that produces them when the branch is first
opened, plus an optional *probe* that answers "has it any?" without reading them all. The probe is asked only for a
row about to be painted, and the answer is remembered. DOS Navigator read a drive's whole tree up front; a
filesystem rooted at `/` cannot afford that. The tree panel loses no fidelity by it, because `THTreeView` is the
collapsible kind (`Parital` on), and its `[+]` and `[-]` are the original's.

**Every measurement is `TTreeView.Draw`'s**, with DOS Navigator's column 0 at the first column inside the frame:

- The root sits at column 2, and each level indents three.
- `│` continues for every ancestor that has siblings below.
- A branch is `├───` or `└───`. In the collapsible view a node with children gets `├─[+] ` or `├─[-] `; in the
  expanded view (`collapsible` off, the dialog kind) it gets `├──┬`.
- **The cursor is ` name ` in the cursor colour, begun one column early** over the last cell of its branch. The
  line is not filled the way a listing's cursor line is.
- The view scrolls sideways to keep the cursor's name in sight.
- Tree lines are always single, whatever frame the widget has, because the original's were.

**The keys are `HandleCommand`'s, but for two:**

- Left and Backspace go to the parent node, and Backspace closes it behind them; Right opens the branch under the
  cursor and goes to its first child, or down a row when there is none. The original moved Left and Right up and
  down, duplicating the arrows beside them; this is a deliberate departure, taken because moving along the tree's
  own structure is what those keys are for everywhere else.
- Space, `+` and `-` open or close the branch under the cursor.
- `*` opens every branch *already read*. The original opened the whole tree, which lazily means the whole disk.
- Ctrl+S searches (`QuickSearch`, now the library's command, shared with the file panel), and so does plain typing
  where `type_to_search` is on -- the dialog and the tree window, as in the original. Ctrl+T's tree turns it off,
  because typing there belongs to the command line, as it does from a panel. The rules are the panel's: forward from
  the cursor, wrapping, case folded, `*`/`?` wildcards (`navml/quick_search.py`'s `name_pattern`, which `Panel` uses
  too), a character that would name nothing refused, Ctrl+S again for the next. The original matched an 8.3 mask,
  which a modern name has no reason to fit.
- Esc ends the search where it stands; any other key ends it and does its job, **Enter included -- it chooses**, as
  DN's did (`CancelSearch` did not clear the event). The panel's Enter only ends its search; the panel follows
  Midnight Commander there, the tree follows DN. `edits_text` is True while it runs, so the command line's
  Enter/Home/End/Tab step aside for Ctrl+T's tree.
- Enter emits `ChosenEvent(node)`.
- A press on a row's `[+]` opens it.

**The quick search is a path, because the tree is lazy.** Searching the rows can only find what has been read, and a
search that cannot find an unopened directory is no search. Two answers were rejected: reading the whole tree in the
background (at `/` that is the disk, network mounts included, stale once finished, and a modern flourish -- DN's way
to find a directory anywhere was *Find file*, an explicit job), and reading unopened branches as the search passes
them (unbounded work per keystroke on the loop, and "not found" costs reading everything). The answer taken is DN's
own (`TREE.PAS`, `SearchForMask`): **`/` descends** -- DN's `\` -- opening the branch matched, putting the cursor
on its first child and confining what is typed next to that branch's children. So `us/lo/bi` reaches
`/usr/local/bin` having read exactly the three directories it names. `/` before anything is typed searches from the
root (DN's leading `\`); Backspace past a `/` climbs back out onto the node it went into (`search_trail`), and the
footer of a framed tree shows the whole path typed (` Search: us/lo/bi `), and the *Directory Tree* window, whose
tree has no frame, puts the same `search_label()` on its own bottom frame. **Confining to the children is a
departure**: DN kept searching forward through every visible row, so a miss among the children could jump anywhere
in the tree; with a refused character it means *you are typing a path*. A new root (Re-read, Ctrl+H) or the
keyboard leaving ends the search.

**Colours** come from two groups. A tree in a dialog takes the Dialogs group's Tree, [104] to [110]. The tree panel
takes the File Manager group's own, [94] to [101], which DOS Navigator gave `CDoubleWindow`. In both, the lines
and ground are *Normal tree* and names are *Normal nodes*. The cursor is *Selected node* while the tree has the
keyboard and *Selected passive* while it has not, which a sheet says with the owner's `:focused` in front of
`::node:selected`. The *default node* slots, the current directory in the expanded view, are carried for when a
dialog tree needs them.

**Ctrl+T is `SwitchView(dtTree)`**, from `DBLWND.PAS`:

- The **passive** panel gives way to the tree, in its place, and the keyboard stays with the active panel. The tree
  is a hidden child of the panels' row, and the manager moves it next to the panel it replaces, since a row lays its
  children out in order.
- Ctrl+T again restores the panel, and gives it the keyboard if the tree had it.
- The tree follows the active panel's directory (`cmChangeTree`), opening the branches *above* it, as `ExpandFor`
  did, but not the directory's own.
- With the keyboard in the tree, **Enter sends the panel there at once**, and a cursor that rests for thirty ticks
  of the 18.2 Hz timer (`NeedLocated`, `Manager.LOCATE_DELAY`) takes the panel with it. Each move restarts the wait.
- Tab moves the keyboard between the panel and the tree.
- Ctrl+R re-reads the tree while it has the keyboard.
- Under the tree, `TTreeInfoView`'s two rows show the path under the cursor and `N files with S bytes`, which is
  `MakeDown`'s wording for the files directly in that directory.

`ListViewer`'s scroll bar is now sized by `rows + header` rather than `height - 2`. That is the same for every
list that was, and it keeps a list that gives up rows of its own (the tree's info band) from running its bar
through them.

**Panel > Change directory (Alt+T) is `TTreeDialog`**, which `ChangeDir` opened as *Choose Directory*:
`navigator/widgets/tree/change_dir_dialog/`. The layout is `TTreeDialog.Init`'s; **the size is not**:

- DN's dialog was a fixed 49 by 17, a sliver of a deep tree on a modern terminal. This one is three quarters of the
  screen's width and four fifths of its height (`modal_width`/`modal_height` bound to the parent, never closer than two columns and one
  row to its edges), and 49 by 17 is the floor -- a departure, at the user's request.
- Every control is placed against the dialog's edges, so at 49 by 17 each rectangle is the original's again: the tree
  fills the left (width - 15 by height - 3, so 34 by 14).
- The path under the cursor is the one row below it: `TDTreeInfoView`, one row tall, so only its first line shows.
  It uses the information pane's colours, [61].
- The buttons stand in a column on the right, 11 wide, 13 cells in from the right edge: `O~K~`, `~D~rive...`,
  `~R~e-read`, `~M~kDir` and `Cancel`. They start at row 2 and are spread down the column, `max(3, (height - 2) // 5)`
  rows apart -- the original's rows 2, 5, 8, 11 and 14 at its own size.
- `Dialog`'s own bottom row of buttons is hidden, since this layout is not that one.

Behaviour:

- OK, or Enter in the tree, answers the directory under the cursor, and the panel that asked goes there. Esc
  answers nothing.
- MkDir makes the new directory where the tree points, as the tree's own `MkDirectory` did, and puts the cursor on
  it. Re-read reads the tree again and keeps the cursor.
- **Drive is shown and disabled.** A POSIX filesystem has one root, and a drive letter has nothing to name.
- The tree here is lazy and collapsible, like the panel's, where `TTreeDialog` read the whole drive and drew the
  expanded kind. That trade was made once for all trees.

**The tree has no frame of its own there, and `ListViewer` learnt to do without one.** Turbo Vision's list views
never had frames; a dialog's or a window's frame was theirs. A file panel has one, so `ListViewer.framed` defaults
on and every list that existed is unchanged. Off, the rows begin at the edge (`inset` is 0) and the scroll bar
takes the last column (`inner_width` is one less than the width), as `TScrollBar` sat beside its view.

**Disk > Directory tree is `TTreeWindow`** (`navigator/widgets/tree/tree_window/`), a window on the desktop titled
*Directory Tree*. DOS Navigator 1.51 **defined this window and never opened it**. Its `cmCreateTree` went to
`OpenTreeWindow` in `DNUTIL.PAS` instead, which asked for a directory with `ChangeDir` and opened a second file
manager there with its tree panel showing. Navigator opens the window as designed, a deliberate choice rather than a
transcription, so two things about it are Navigator's own: its size, which is `Window`'s default because nothing
ever gave it bounds, and what Enter does.

- **The layout is `TTreeWindow.Init`'s.** The tree fills the inside of the frame less two rows. The two
  `TTreeInfoView` rows below it show the path and `N files with S bytes`. The scroll bar stands on the frame's right
  edge. That is `DirectoryTree` without its frame, one column into the window, so its last column is the frame's.
- **It is coloured with the dialog palette**, because `TTreeWindow.GetPalette` returns `CTreeDialog`: a dialog's
  frame, the Dialogs group's Tree [104]–[110], and the information pane [61] for the two rows.
- **Esc closes it**, as `TTreeWindow.HandleEvent` did, through the `CloseWindow` command in its key table. Ctrl+R
  and Alt+R re-read its tree.
- **Enter sends the file manager's active panel to the directory, and the keyboard stays in the tree.** The window
  does not handle the tree's `ChosenEvent`: its generated stub declines, and the event walks up to `Shell`, which is
  the one thing that knows where the file manager is. The manager's own tree and *Choose Directory* both claim
  theirs first.

A frameless list fills only its rows' columns. The scroll bar paints its own column, and below the bar's end the
cells are whatever the list stands on, which is the window's frame here.

