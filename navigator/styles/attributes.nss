/*
 * The text attributes of every entry DOS Navigator's Colors dialog exposes.
 *
 * DN's palette was colours alone: an attribute byte, foreground and
 * background.  A terminal draws more -- bold, dim, italic, underline and
 * reverse -- and Options > Colors sets them per entry, as it sets the
 * colours.  The rules in navigator.nss read `$<entry>-bold' and the rest
 * beside `$<entry>-fg', so these are their defaults: loaded after the rules
 * and before the theme, which may redefine any of them, as a user palette
 * (Options > Colors, Store palette) does.
 *
 * Every default is `inherit', which drops the declaration, so an entry
 * says nothing of an attribute until it is given one and the cursor row
 * stays bold over a directory.  The three set are what navigator.nss set by
 * hand before there were variables: the directory row bold, and a tagged
 * row (cursor or not) not bold whatever it is tagged over.
 */


/* -- Timer ----------------------------------------------------------------- */
$desktop-bold: inherit; $desktop-dim: inherit; $desktop-italic: inherit; $desktop-underline: inherit; $desktop-reverse: inherit;

/* -- Menus ----------------------------------------------------------------- */
$bar-bold: inherit; $bar-dim: inherit; $bar-italic: inherit; $bar-underline: inherit; $bar-reverse: inherit;
$bar-disabled-bold: inherit; $bar-disabled-dim: inherit; $bar-disabled-italic: inherit; $bar-disabled-underline: inherit; $bar-disabled-reverse: inherit;
$bar-key-bold: inherit; $bar-key-dim: inherit; $bar-key-italic: inherit; $bar-key-underline: inherit; $bar-key-reverse: inherit;
$bar-selected-bold: inherit; $bar-selected-dim: inherit; $bar-selected-italic: inherit; $bar-selected-underline: inherit; $bar-selected-reverse: inherit;
$bar-selected-disabled-bold: inherit; $bar-selected-disabled-dim: inherit; $bar-selected-disabled-italic: inherit; $bar-selected-disabled-underline: inherit; $bar-selected-disabled-reverse: inherit;
$bar-selected-key-bold: inherit; $bar-selected-key-dim: inherit; $bar-selected-key-italic: inherit; $bar-selected-key-underline: inherit; $bar-selected-key-reverse: inherit;

/* -- Dialogs --------------------------------------------------------------- */
$dialog-frame-background-bold: inherit; $dialog-frame-background-dim: inherit; $dialog-frame-background-italic: inherit; $dialog-frame-background-underline: inherit; $dialog-frame-background-reverse: inherit;
$dialog-frame-icons-bold: inherit; $dialog-frame-icons-dim: inherit; $dialog-frame-icons-italic: inherit; $dialog-frame-icons-underline: inherit; $dialog-frame-icons-reverse: inherit;
$dialog-scroll-bar-page-bold: inherit; $dialog-scroll-bar-page-dim: inherit; $dialog-scroll-bar-page-italic: inherit; $dialog-scroll-bar-page-underline: inherit; $dialog-scroll-bar-page-reverse: inherit;
$dialog-scroll-bar-icons-bold: inherit; $dialog-scroll-bar-icons-dim: inherit; $dialog-scroll-bar-icons-italic: inherit; $dialog-scroll-bar-icons-underline: inherit; $dialog-scroll-bar-icons-reverse: inherit;
$dialog-static-text-bold: inherit; $dialog-static-text-dim: inherit; $dialog-static-text-italic: inherit; $dialog-static-text-underline: inherit; $dialog-static-text-reverse: inherit;
$dialog-label-normal-bold: inherit; $dialog-label-normal-dim: inherit; $dialog-label-normal-italic: inherit; $dialog-label-normal-underline: inherit; $dialog-label-normal-reverse: inherit;
$dialog-label-selected-bold: inherit; $dialog-label-selected-dim: inherit; $dialog-label-selected-italic: inherit; $dialog-label-selected-underline: inherit; $dialog-label-selected-reverse: inherit;
$dialog-label-shortcut-bold: inherit; $dialog-label-shortcut-dim: inherit; $dialog-label-shortcut-italic: inherit; $dialog-label-shortcut-underline: inherit; $dialog-label-shortcut-reverse: inherit;
$dialog-button-normal-bold: inherit; $dialog-button-normal-dim: inherit; $dialog-button-normal-italic: inherit; $dialog-button-normal-underline: inherit; $dialog-button-normal-reverse: inherit;
$dialog-button-default-bold: inherit; $dialog-button-default-dim: inherit; $dialog-button-default-italic: inherit; $dialog-button-default-underline: inherit; $dialog-button-default-reverse: inherit;
$dialog-button-selected-bold: inherit; $dialog-button-selected-dim: inherit; $dialog-button-selected-italic: inherit; $dialog-button-selected-underline: inherit; $dialog-button-selected-reverse: inherit;
$dialog-button-disabled-bold: inherit; $dialog-button-disabled-dim: inherit; $dialog-button-disabled-italic: inherit; $dialog-button-disabled-underline: inherit; $dialog-button-disabled-reverse: inherit;
$dialog-button-shortcut-bold: inherit; $dialog-button-shortcut-dim: inherit; $dialog-button-shortcut-italic: inherit; $dialog-button-shortcut-underline: inherit; $dialog-button-shortcut-reverse: inherit;
$dialog-shortcut-selected-bold: inherit; $dialog-shortcut-selected-dim: inherit; $dialog-shortcut-selected-italic: inherit; $dialog-shortcut-selected-underline: inherit; $dialog-shortcut-selected-reverse: inherit;
$dialog-shortcut-default-bold: inherit; $dialog-shortcut-default-dim: inherit; $dialog-shortcut-default-italic: inherit; $dialog-shortcut-default-underline: inherit; $dialog-shortcut-default-reverse: inherit;
$dialog-button-shadow-bold: inherit; $dialog-button-shadow-dim: inherit; $dialog-button-shadow-italic: inherit; $dialog-button-shadow-underline: inherit; $dialog-button-shadow-reverse: inherit;
$dialog-cluster-normal-bold: inherit; $dialog-cluster-normal-dim: inherit; $dialog-cluster-normal-italic: inherit; $dialog-cluster-normal-underline: inherit; $dialog-cluster-normal-reverse: inherit;
$dialog-cluster-selected-bold: inherit; $dialog-cluster-selected-dim: inherit; $dialog-cluster-selected-italic: inherit; $dialog-cluster-selected-underline: inherit; $dialog-cluster-selected-reverse: inherit;
$dialog-cluster-shortcut-bold: inherit; $dialog-cluster-shortcut-dim: inherit; $dialog-cluster-shortcut-italic: inherit; $dialog-cluster-shortcut-underline: inherit; $dialog-cluster-shortcut-reverse: inherit;
$dialog-input-normal-bold: inherit; $dialog-input-normal-dim: inherit; $dialog-input-normal-italic: inherit; $dialog-input-normal-underline: inherit; $dialog-input-normal-reverse: inherit;
$dialog-input-selected-bold: inherit; $dialog-input-selected-dim: inherit; $dialog-input-selected-italic: inherit; $dialog-input-selected-underline: inherit; $dialog-input-selected-reverse: inherit;
$dialog-input-arrow-bold: inherit; $dialog-input-arrow-dim: inherit; $dialog-input-arrow-italic: inherit; $dialog-input-arrow-underline: inherit; $dialog-input-arrow-reverse: inherit;
$dialog-history-button-bold: inherit; $dialog-history-button-dim: inherit; $dialog-history-button-italic: inherit; $dialog-history-button-underline: inherit; $dialog-history-button-reverse: inherit;
$dialog-history-sides-bold: inherit; $dialog-history-sides-dim: inherit; $dialog-history-sides-italic: inherit; $dialog-history-sides-underline: inherit; $dialog-history-sides-reverse: inherit;
$dialog-history-bar-page-bold: inherit; $dialog-history-bar-page-dim: inherit; $dialog-history-bar-page-italic: inherit; $dialog-history-bar-page-underline: inherit; $dialog-history-bar-page-reverse: inherit;
$dialog-history-bar-icons-bold: inherit; $dialog-history-bar-icons-dim: inherit; $dialog-history-bar-icons-italic: inherit; $dialog-history-bar-icons-underline: inherit; $dialog-history-bar-icons-reverse: inherit;
$dialog-list-normal-bold: inherit; $dialog-list-normal-dim: inherit; $dialog-list-normal-italic: inherit; $dialog-list-normal-underline: inherit; $dialog-list-normal-reverse: inherit;
$dialog-list-focused-bold: inherit; $dialog-list-focused-dim: inherit; $dialog-list-focused-italic: inherit; $dialog-list-focused-underline: inherit; $dialog-list-focused-reverse: inherit;
$dialog-list-selected-bold: inherit; $dialog-list-selected-dim: inherit; $dialog-list-selected-italic: inherit; $dialog-list-selected-underline: inherit; $dialog-list-selected-reverse: inherit;
$dialog-list-divider-bold: inherit; $dialog-list-divider-dim: inherit; $dialog-list-divider-italic: inherit; $dialog-list-divider-underline: inherit; $dialog-list-divider-reverse: inherit;
$dialog-information-pane-bold: inherit; $dialog-information-pane-dim: inherit; $dialog-information-pane-italic: inherit; $dialog-information-pane-underline: inherit; $dialog-information-pane-reverse: inherit;

/* -- Tree ------------------------------------------------------------------ */
$dialog-tree-normal-tree-bold: inherit; $dialog-tree-normal-tree-dim: inherit; $dialog-tree-normal-tree-italic: inherit; $dialog-tree-normal-tree-underline: inherit; $dialog-tree-normal-tree-reverse: inherit;
$dialog-tree-normal-nodes-bold: inherit; $dialog-tree-normal-nodes-dim: inherit; $dialog-tree-normal-nodes-italic: inherit; $dialog-tree-normal-nodes-underline: inherit; $dialog-tree-normal-nodes-reverse: inherit;
$dialog-tree-selected-node-bold: inherit; $dialog-tree-selected-node-dim: inherit; $dialog-tree-selected-node-italic: inherit; $dialog-tree-selected-node-underline: inherit; $dialog-tree-selected-node-reverse: inherit;
$dialog-tree-default-node-bold: inherit; $dialog-tree-default-node-dim: inherit; $dialog-tree-default-node-italic: inherit; $dialog-tree-default-node-underline: inherit; $dialog-tree-default-node-reverse: inherit;
$dialog-tree-selected-default-bold: inherit; $dialog-tree-selected-default-dim: inherit; $dialog-tree-selected-default-italic: inherit; $dialog-tree-selected-default-underline: inherit; $dialog-tree-selected-default-reverse: inherit;
$dialog-tree-selected-passive-bold: inherit; $dialog-tree-selected-passive-dim: inherit; $dialog-tree-selected-passive-italic: inherit; $dialog-tree-selected-passive-underline: inherit; $dialog-tree-selected-passive-reverse: inherit;
$dialog-tree-selected-def-passive-bold: inherit; $dialog-tree-selected-def-passive-dim: inherit; $dialog-tree-selected-def-passive-italic: inherit; $dialog-tree-selected-def-passive-underline: inherit; $dialog-tree-selected-def-passive-reverse: inherit;

/* -- File Manager ---------------------------------------------------------- */
$frame-bold: inherit; $frame-dim: inherit; $frame-italic: inherit; $frame-underline: inherit; $frame-reverse: inherit;
$active-frame-bold: inherit; $active-frame-dim: inherit; $active-frame-italic: inherit; $active-frame-underline: inherit; $active-frame-reverse: inherit;
$frame-icon-bold: inherit; $frame-icon-dim: inherit; $frame-icon-italic: inherit; $frame-icon-underline: inherit; $frame-icon-reverse: inherit;
$scrollbar-page-bold: inherit; $scrollbar-page-dim: inherit; $scrollbar-page-italic: inherit; $scrollbar-page-underline: inherit; $scrollbar-page-reverse: inherit;
$scrollbar-arrow-bold: inherit; $scrollbar-arrow-dim: inherit; $scrollbar-arrow-italic: inherit; $scrollbar-arrow-underline: inherit; $scrollbar-arrow-reverse: inherit;

/* -- File Panel ------------------------------------------------------------ */
$panel-bold: inherit; $panel-dim: inherit; $panel-italic: inherit; $panel-underline: inherit; $panel-reverse: inherit;
$marked-bold: false; $marked-dim: inherit; $marked-italic: inherit; $marked-underline: inherit; $marked-reverse: inherit;
$cursor-bold: inherit; $cursor-dim: inherit; $cursor-italic: inherit; $cursor-underline: inherit; $cursor-reverse: inherit;
$marked-cursor-bold: false; $marked-cursor-dim: inherit; $marked-cursor-italic: inherit; $marked-cursor-underline: inherit; $marked-cursor-reverse: inherit;
$divider-bold: inherit; $divider-dim: inherit; $divider-italic: inherit; $divider-underline: inherit; $divider-reverse: inherit;
$active-title-bold: inherit; $active-title-dim: inherit; $active-title-italic: inherit; $active-title-underline: inherit; $active-title-reverse: inherit;
$title-bold: inherit; $title-dim: inherit; $title-italic: inherit; $title-underline: inherit; $title-reverse: inherit;
$column-title-bold: inherit; $column-title-dim: inherit; $column-title-italic: inherit; $column-title-underline: inherit; $column-title-reverse: inherit;

/* -- Highlight ------------------------------------------------------------- */
$directory-bold: true; $directory-dim: inherit; $directory-italic: inherit; $directory-underline: inherit; $directory-reverse: inherit;
$executable-bold: inherit; $executable-dim: inherit; $executable-italic: inherit; $executable-underline: inherit; $executable-reverse: inherit;
$archive-bold: inherit; $archive-dim: inherit; $archive-italic: inherit; $archive-underline: inherit; $archive-reverse: inherit;
$highlight-custom-1-bold: inherit; $highlight-custom-1-dim: inherit; $highlight-custom-1-italic: inherit; $highlight-custom-1-underline: inherit; $highlight-custom-1-reverse: inherit;
$highlight-custom-2-bold: inherit; $highlight-custom-2-dim: inherit; $highlight-custom-2-italic: inherit; $highlight-custom-2-underline: inherit; $highlight-custom-2-reverse: inherit;
$highlight-custom-3-bold: inherit; $highlight-custom-3-dim: inherit; $highlight-custom-3-italic: inherit; $highlight-custom-3-underline: inherit; $highlight-custom-3-reverse: inherit;
$highlight-custom-4-bold: inherit; $highlight-custom-4-dim: inherit; $highlight-custom-4-italic: inherit; $highlight-custom-4-underline: inherit; $highlight-custom-4-reverse: inherit;
$highlight-custom-5-bold: inherit; $highlight-custom-5-dim: inherit; $highlight-custom-5-italic: inherit; $highlight-custom-5-underline: inherit; $highlight-custom-5-reverse: inherit;

/* -- Drive Line ------------------------------------------------------------ */
$drive-line-drive-letters-bold: inherit; $drive-line-drive-letters-dim: inherit; $drive-line-drive-letters-italic: inherit; $drive-line-drive-letters-underline: inherit; $drive-line-drive-letters-reverse: inherit;
$drive-line-drive-selected-bold: inherit; $drive-line-drive-selected-dim: inherit; $drive-line-drive-selected-italic: inherit; $drive-line-drive-selected-underline: inherit; $drive-line-drive-selected-reverse: inherit;
$drive-line-frame-bold: inherit; $drive-line-frame-dim: inherit; $drive-line-frame-italic: inherit; $drive-line-frame-underline: inherit; $drive-line-frame-reverse: inherit;

/* -- Info ------------------------------------------------------------------ */
$info-current-file-bold: inherit; $info-current-file-dim: inherit; $info-current-file-italic: inherit; $info-current-file-underline: inherit; $info-current-file-reverse: inherit;
$info-selected-text-bold: inherit; $info-selected-text-dim: inherit; $info-selected-text-italic: inherit; $info-selected-text-underline: inherit; $info-selected-text-reverse: inherit;
$info-selected-numbers-bold: inherit; $info-selected-numbers-dim: inherit; $info-selected-numbers-italic: inherit; $info-selected-numbers-underline: inherit; $info-selected-numbers-reverse: inherit;
$info-totals-text-bold: inherit; $info-totals-text-dim: inherit; $info-totals-text-italic: inherit; $info-totals-text-underline: inherit; $info-totals-text-reverse: inherit;
$info-totals-numbers-bold: inherit; $info-totals-numbers-dim: inherit; $info-totals-numbers-italic: inherit; $info-totals-numbers-underline: inherit; $info-totals-numbers-reverse: inherit;
$info-free-space-text-bold: inherit; $info-free-space-text-dim: inherit; $info-free-space-text-italic: inherit; $info-free-space-text-underline: inherit; $info-free-space-text-reverse: inherit;
$info-free-space-numbers-bold: inherit; $info-free-space-numbers-dim: inherit; $info-free-space-numbers-italic: inherit; $info-free-space-numbers-underline: inherit; $info-free-space-numbers-reverse: inherit;

/* -- Tree ------------------------------------------------------------------ */
$tree-normal-tree-bold: inherit; $tree-normal-tree-dim: inherit; $tree-normal-tree-italic: inherit; $tree-normal-tree-underline: inherit; $tree-normal-tree-reverse: inherit;
$tree-normal-nodes-bold: inherit; $tree-normal-nodes-dim: inherit; $tree-normal-nodes-italic: inherit; $tree-normal-nodes-underline: inherit; $tree-normal-nodes-reverse: inherit;
$tree-selected-node-bold: inherit; $tree-selected-node-dim: inherit; $tree-selected-node-italic: inherit; $tree-selected-node-underline: inherit; $tree-selected-node-reverse: inherit;
$tree-default-node-bold: inherit; $tree-default-node-dim: inherit; $tree-default-node-italic: inherit; $tree-default-node-underline: inherit; $tree-default-node-reverse: inherit;
$tree-selected-default-bold: inherit; $tree-selected-default-dim: inherit; $tree-selected-default-italic: inherit; $tree-selected-default-underline: inherit; $tree-selected-default-reverse: inherit;
$tree-selected-passive-bold: inherit; $tree-selected-passive-dim: inherit; $tree-selected-passive-italic: inherit; $tree-selected-passive-underline: inherit; $tree-selected-passive-reverse: inherit;
$tree-selected-def-passive-bold: inherit; $tree-selected-def-passive-dim: inherit; $tree-selected-def-passive-italic: inherit; $tree-selected-def-passive-underline: inherit; $tree-selected-def-passive-reverse: inherit;
$tree-info-box-bold: inherit; $tree-info-box-dim: inherit; $tree-info-box-italic: inherit; $tree-info-box-underline: inherit; $tree-info-box-reverse: inherit;

/* -- Quick View ------------------------------------------------------------ */
$quick-view-normal-text-bold: inherit; $quick-view-normal-text-dim: inherit; $quick-view-normal-text-italic: inherit; $quick-view-normal-text-underline: inherit; $quick-view-normal-text-reverse: inherit;
$quick-view-selected-text-bold: inherit; $quick-view-selected-text-dim: inherit; $quick-view-selected-text-italic: inherit; $quick-view-selected-text-underline: inherit; $quick-view-selected-text-reverse: inherit;

/* -- Disk Info ------------------------------------------------------------- */
$disk-info-normal-text-bold: inherit; $disk-info-normal-text-dim: inherit; $disk-info-normal-text-italic: inherit; $disk-info-normal-text-underline: inherit; $disk-info-normal-text-reverse: inherit;
$disk-info-highlighted-text-bold: inherit; $disk-info-highlighted-text-dim: inherit; $disk-info-highlighted-text-italic: inherit; $disk-info-highlighted-text-underline: inherit; $disk-info-highlighted-text-reverse: inherit;

/* -- File Viewer ----------------------------------------------------------- */
$viewer-frame-passive-bold: inherit; $viewer-frame-passive-dim: inherit; $viewer-frame-passive-italic: inherit; $viewer-frame-passive-underline: inherit; $viewer-frame-passive-reverse: inherit;
$viewer-frame-active-bold: inherit; $viewer-frame-active-dim: inherit; $viewer-frame-active-italic: inherit; $viewer-frame-active-underline: inherit; $viewer-frame-active-reverse: inherit;
$viewer-frame-icons-bold: inherit; $viewer-frame-icons-dim: inherit; $viewer-frame-icons-italic: inherit; $viewer-frame-icons-underline: inherit; $viewer-frame-icons-reverse: inherit;
$viewer-scroll-bar-page-bold: inherit; $viewer-scroll-bar-page-dim: inherit; $viewer-scroll-bar-page-italic: inherit; $viewer-scroll-bar-page-underline: inherit; $viewer-scroll-bar-page-reverse: inherit;
$viewer-scroll-bar-icons-bold: inherit; $viewer-scroll-bar-icons-dim: inherit; $viewer-scroll-bar-icons-italic: inherit; $viewer-scroll-bar-icons-underline: inherit; $viewer-scroll-bar-icons-reverse: inherit;
$viewer-normal-text-bold: inherit; $viewer-normal-text-dim: inherit; $viewer-normal-text-italic: inherit; $viewer-normal-text-underline: inherit; $viewer-normal-text-reverse: inherit;
$viewer-selected-text-bold: inherit; $viewer-selected-text-dim: inherit; $viewer-selected-text-italic: inherit; $viewer-selected-text-underline: inherit; $viewer-selected-text-reverse: inherit;

/* -- Editor/Spreadsheet ---------------------------------------------------- */
$editor-frame-passive-bold: inherit; $editor-frame-passive-dim: inherit; $editor-frame-passive-italic: inherit; $editor-frame-passive-underline: inherit; $editor-frame-passive-reverse: inherit;
$editor-frame-active-bold: inherit; $editor-frame-active-dim: inherit; $editor-frame-active-italic: inherit; $editor-frame-active-underline: inherit; $editor-frame-active-reverse: inherit;
$editor-frame-icons-bold: inherit; $editor-frame-icons-dim: inherit; $editor-frame-icons-italic: inherit; $editor-frame-icons-underline: inherit; $editor-frame-icons-reverse: inherit;
$editor-frame-title-bold: inherit; $editor-frame-title-dim: inherit; $editor-frame-title-italic: inherit; $editor-frame-title-underline: inherit; $editor-frame-title-reverse: inherit;
$editor-scroll-bar-page-bold: inherit; $editor-scroll-bar-page-dim: inherit; $editor-scroll-bar-page-italic: inherit; $editor-scroll-bar-page-underline: inherit; $editor-scroll-bar-page-reverse: inherit;
$editor-scroll-bar-icons-bold: inherit; $editor-scroll-bar-icons-dim: inherit; $editor-scroll-bar-icons-italic: inherit; $editor-scroll-bar-icons-underline: inherit; $editor-scroll-bar-icons-reverse: inherit;
$editor-normal-text-bold: inherit; $editor-normal-text-dim: inherit; $editor-normal-text-italic: inherit; $editor-normal-text-underline: inherit; $editor-normal-text-reverse: inherit;
$editor-selected-text-bold: inherit; $editor-selected-text-dim: inherit; $editor-selected-text-italic: inherit; $editor-selected-text-underline: inherit; $editor-selected-text-reverse: inherit;

/* -- Highlight ------------------------------------------------------------- */
$editor-highlight-comments-bold: inherit; $editor-highlight-comments-dim: inherit; $editor-highlight-comments-italic: inherit; $editor-highlight-comments-underline: inherit; $editor-highlight-comments-reverse: inherit;
$editor-highlight-symbols-bold: inherit; $editor-highlight-symbols-dim: inherit; $editor-highlight-symbols-italic: inherit; $editor-highlight-symbols-underline: inherit; $editor-highlight-symbols-reverse: inherit;
$editor-highlight-strings-bold: inherit; $editor-highlight-strings-dim: inherit; $editor-highlight-strings-italic: inherit; $editor-highlight-strings-underline: inherit; $editor-highlight-strings-reverse: inherit;
$editor-highlight-numbers-bold: inherit; $editor-highlight-numbers-dim: inherit; $editor-highlight-numbers-italic: inherit; $editor-highlight-numbers-underline: inherit; $editor-highlight-numbers-reverse: inherit;
$editor-highlight-current-line-bold: inherit; $editor-highlight-current-line-dim: inherit; $editor-highlight-current-line-italic: inherit; $editor-highlight-current-line-underline: inherit; $editor-highlight-current-line-reverse: inherit;
$editor-highlight-cur-line-comments-bold: inherit; $editor-highlight-cur-line-comments-dim: inherit; $editor-highlight-cur-line-comments-italic: inherit; $editor-highlight-cur-line-comments-underline: inherit; $editor-highlight-cur-line-comments-reverse: inherit;
$editor-highlight-current-line-selected-bold: inherit; $editor-highlight-current-line-selected-dim: inherit; $editor-highlight-current-line-selected-italic: inherit; $editor-highlight-current-line-selected-underline: inherit; $editor-highlight-current-line-selected-reverse: inherit;
$editor-highlight-current-column-bold: inherit; $editor-highlight-current-column-dim: inherit; $editor-highlight-current-column-italic: inherit; $editor-highlight-current-column-underline: inherit; $editor-highlight-current-column-reverse: inherit;

/* -- Menu ------------------------------------------------------------------ */
$editor-menu-normal-bold: inherit; $editor-menu-normal-dim: inherit; $editor-menu-normal-italic: inherit; $editor-menu-normal-underline: inherit; $editor-menu-normal-reverse: inherit;
$editor-menu-disabled-bold: inherit; $editor-menu-disabled-dim: inherit; $editor-menu-disabled-italic: inherit; $editor-menu-disabled-underline: inherit; $editor-menu-disabled-reverse: inherit;
$editor-menu-shortcut-bold: inherit; $editor-menu-shortcut-dim: inherit; $editor-menu-shortcut-italic: inherit; $editor-menu-shortcut-underline: inherit; $editor-menu-shortcut-reverse: inherit;
$editor-menu-selected-bold: inherit; $editor-menu-selected-dim: inherit; $editor-menu-selected-italic: inherit; $editor-menu-selected-underline: inherit; $editor-menu-selected-reverse: inherit;
$editor-menu-selected-disabled-bold: inherit; $editor-menu-selected-disabled-dim: inherit; $editor-menu-selected-disabled-italic: inherit; $editor-menu-selected-disabled-underline: inherit; $editor-menu-selected-disabled-reverse: inherit;
$editor-menu-shortcut-selected-bold: inherit; $editor-menu-shortcut-selected-dim: inherit; $editor-menu-shortcut-selected-italic: inherit; $editor-menu-shortcut-selected-underline: inherit; $editor-menu-shortcut-selected-reverse: inherit;

/* -- Disk Fixer ------------------------------------------------------------ */
$fixer-frame-passive-bold: inherit; $fixer-frame-passive-dim: inherit; $fixer-frame-passive-italic: inherit; $fixer-frame-passive-underline: inherit; $fixer-frame-passive-reverse: inherit;
$fixer-frame-active-bold: inherit; $fixer-frame-active-dim: inherit; $fixer-frame-active-italic: inherit; $fixer-frame-active-underline: inherit; $fixer-frame-active-reverse: inherit;
$fixer-frame-icons-bold: inherit; $fixer-frame-icons-dim: inherit; $fixer-frame-icons-italic: inherit; $fixer-frame-icons-underline: inherit; $fixer-frame-icons-reverse: inherit;
$fixer-frame-title-bold: inherit; $fixer-frame-title-dim: inherit; $fixer-frame-title-italic: inherit; $fixer-frame-title-underline: inherit; $fixer-frame-title-reverse: inherit;
$fixer-scroll-bar-page-bold: inherit; $fixer-scroll-bar-page-dim: inherit; $fixer-scroll-bar-page-italic: inherit; $fixer-scroll-bar-page-underline: inherit; $fixer-scroll-bar-page-reverse: inherit;
$fixer-scroll-bar-icons-bold: inherit; $fixer-scroll-bar-icons-dim: inherit; $fixer-scroll-bar-icons-italic: inherit; $fixer-scroll-bar-icons-underline: inherit; $fixer-scroll-bar-icons-reverse: inherit;
$fixer-normal-text-bold: inherit; $fixer-normal-text-dim: inherit; $fixer-normal-text-italic: inherit; $fixer-normal-text-underline: inherit; $fixer-normal-text-reverse: inherit;
$fixer-selected-text-bold: inherit; $fixer-selected-text-dim: inherit; $fixer-selected-text-italic: inherit; $fixer-selected-text-underline: inherit; $fixer-selected-text-reverse: inherit;
$fixer-sector-title-bold: inherit; $fixer-sector-title-dim: inherit; $fixer-sector-title-italic: inherit; $fixer-sector-title-underline: inherit; $fixer-sector-title-reverse: inherit;
$fixer-edit-line-bold: inherit; $fixer-edit-line-dim: inherit; $fixer-edit-line-italic: inherit; $fixer-edit-line-underline: inherit; $fixer-edit-line-reverse: inherit;

/* -- Menu ------------------------------------------------------------------ */
$fixer-menu-normal-bold: inherit; $fixer-menu-normal-dim: inherit; $fixer-menu-normal-italic: inherit; $fixer-menu-normal-underline: inherit; $fixer-menu-normal-reverse: inherit;
$fixer-menu-disabled-bold: inherit; $fixer-menu-disabled-dim: inherit; $fixer-menu-disabled-italic: inherit; $fixer-menu-disabled-underline: inherit; $fixer-menu-disabled-reverse: inherit;
$fixer-menu-shortcut-bold: inherit; $fixer-menu-shortcut-dim: inherit; $fixer-menu-shortcut-italic: inherit; $fixer-menu-shortcut-underline: inherit; $fixer-menu-shortcut-reverse: inherit;
$fixer-menu-selected-bold: inherit; $fixer-menu-selected-dim: inherit; $fixer-menu-selected-italic: inherit; $fixer-menu-selected-underline: inherit; $fixer-menu-selected-reverse: inherit;
$fixer-menu-selected-disabled-bold: inherit; $fixer-menu-selected-disabled-dim: inherit; $fixer-menu-selected-disabled-italic: inherit; $fixer-menu-selected-disabled-underline: inherit; $fixer-menu-selected-disabled-reverse: inherit;
$fixer-menu-shortcut-selected-bold: inherit; $fixer-menu-shortcut-selected-dim: inherit; $fixer-menu-shortcut-selected-italic: inherit; $fixer-menu-shortcut-selected-underline: inherit; $fixer-menu-shortcut-selected-reverse: inherit;

/* -- Terminal -------------------------------------------------------------- */
$terminal-frame-passive-bold: inherit; $terminal-frame-passive-dim: inherit; $terminal-frame-passive-italic: inherit; $terminal-frame-passive-underline: inherit; $terminal-frame-passive-reverse: inherit;
$terminal-frame-active-bold: inherit; $terminal-frame-active-dim: inherit; $terminal-frame-active-italic: inherit; $terminal-frame-active-underline: inherit; $terminal-frame-active-reverse: inherit;
$terminal-frame-icons-bold: inherit; $terminal-frame-icons-dim: inherit; $terminal-frame-icons-italic: inherit; $terminal-frame-icons-underline: inherit; $terminal-frame-icons-reverse: inherit;
$terminal-scroll-bar-page-bold: inherit; $terminal-scroll-bar-page-dim: inherit; $terminal-scroll-bar-page-italic: inherit; $terminal-scroll-bar-page-underline: inherit; $terminal-scroll-bar-page-reverse: inherit;
$terminal-scroll-bar-icons-bold: inherit; $terminal-scroll-bar-icons-dim: inherit; $terminal-scroll-bar-icons-italic: inherit; $terminal-scroll-bar-icons-underline: inherit; $terminal-scroll-bar-icons-reverse: inherit;

/* -- dBase viewer ---------------------------------------------------------- */
$dbase-frame-passive-bold: inherit; $dbase-frame-passive-dim: inherit; $dbase-frame-passive-italic: inherit; $dbase-frame-passive-underline: inherit; $dbase-frame-passive-reverse: inherit;
$dbase-frame-active-bold: inherit; $dbase-frame-active-dim: inherit; $dbase-frame-active-italic: inherit; $dbase-frame-active-underline: inherit; $dbase-frame-active-reverse: inherit;
$dbase-frame-icons-bold: inherit; $dbase-frame-icons-dim: inherit; $dbase-frame-icons-italic: inherit; $dbase-frame-icons-underline: inherit; $dbase-frame-icons-reverse: inherit;
$dbase-fields-titles-bold: inherit; $dbase-fields-titles-dim: inherit; $dbase-fields-titles-italic: inherit; $dbase-fields-titles-underline: inherit; $dbase-fields-titles-reverse: inherit;
$dbase-normal-text-bold: inherit; $dbase-normal-text-dim: inherit; $dbase-normal-text-italic: inherit; $dbase-normal-text-underline: inherit; $dbase-normal-text-reverse: inherit;
$dbase-cursor-bold: inherit; $dbase-cursor-dim: inherit; $dbase-cursor-italic: inherit; $dbase-cursor-underline: inherit; $dbase-cursor-reverse: inherit;

/* -- Navigator's own, which DN had no entry for (palette.DERIVED) ------- */
$image-bold: inherit; $image-dim: inherit; $image-italic: inherit; $image-underline: inherit; $image-reverse: inherit;
$media-bold: inherit; $media-dim: inherit; $media-italic: inherit; $media-underline: inherit; $media-reverse: inherit;
$document-bold: inherit; $document-dim: inherit; $document-italic: inherit; $document-underline: inherit; $document-reverse: inherit;
$stale-link-bold: inherit; $stale-link-dim: inherit; $stale-link-italic: inherit; $stale-link-underline: inherit; $stale-link-reverse: inherit;
$source-bold: inherit; $source-dim: inherit; $source-italic: inherit; $source-underline: inherit; $source-reverse: inherit;
$symlink-bold: inherit; $symlink-dim: inherit; $symlink-italic: inherit; $symlink-underline: inherit; $symlink-reverse: inherit;
$device-bold: inherit; $device-dim: inherit; $device-italic: inherit; $device-underline: inherit; $device-reverse: inherit;
$special-bold: inherit; $special-dim: inherit; $special-italic: inherit; $special-underline: inherit; $special-reverse: inherit;
$temp-bold: inherit; $temp-dim: inherit; $temp-italic: inherit; $temp-underline: inherit; $temp-reverse: inherit;
$root-title-bold: inherit; $root-title-dim: inherit; $root-title-italic: inherit; $root-title-underline: inherit; $root-title-reverse: inherit;
