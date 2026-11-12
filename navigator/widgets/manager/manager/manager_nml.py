# navml: generated
"""Generated from ``manager.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.events import Event as _Event
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.manager.commands import AdvancedFilter, AlternateEdit, AlternateView, ArcTest, ArchiveFiles    # manager.nml:1
from navigator.widgets.manager.commands import CalculateChecksums, Calculator, ChangeAttributes, ChangeDirectory    # manager.nml:2
from navigator.widgets.manager.commands import ChangeDrive, ChangeInactive, ChangeLeft, ChangeRight, ClearClipboard    # manager.nml:3
from navigator.widgets.manager.commands import CompareDir, ConvertText, Copy, CountLength, CutToClipboard, DecryptFiles    # manager.nml:4
from navigator.widgets.manager.commands import Delete, DeleteSingle, DiffFiles, DirBranch, DirHistory, DiskInfo, Edit    # manager.nml:5
from navigator.widgets.manager.commands import EditLinkTarget, EditNamed, EncryptFiles, EnterWithoutArchive    # manager.nml:6
from navigator.widgets.manager.commands import EqualizePanels, ExtractArchive, ExtractTo, FastRename, FindDuplicates    # manager.nml:7
from navigator.widgets.manager.commands import FindFile, GoInto, GoRoot, GoToFile, GoToTreeDirectory, HideInactive    # manager.nml:8
from navigator.widgets.manager.commands import HideRight, InvertSelection, JumpToDirectory, LinkAbsolute, LinkRelative    # manager.nml:9
from navigator.widgets.manager.commands import ListOfDirs, MakeDirectory, MakeLink, MakeList, MoveSeparator, MultiRename    # manager.nml:10
from navigator.widgets.manager.commands import OpenArchive, PanelSetup, Panelize, PasteFromClipboard, PrintFile    # manager.nml:11
from navigator.widgets.manager.commands import PutInClipboard, QuickRename, QuickView, ReadFileList, RememberDirectory    # manager.nml:12
from navigator.widgets.manager.commands import RememberedDirectories, RenameMove, ReplaceInFiles, Rescan, RestoreTrash    # manager.nml:13
from navigator.widgets.manager.commands import ScrollNames, SelectAll, SelectBadNames, SelectBrokenLinks, SelectGroup    # manager.nml:14
from navigator.widgets.manager.commands import SelectSimilar, SetupColumns, ShowHardLinks, SortBy, SplitCombine    # manager.nml:15
from navigator.widgets.manager.commands import StoreQuickDir, SwapPanels, SwitchPanel, ToggleHidden, ToggleInfoLines    # manager.nml:16
from navigator.widgets.manager.commands import ToggleMark, ToggleMiller, ToggleShowMode, ToggleTree, Undo, UnmountImage    # manager.nml:17
from navigator.widgets.manager.commands import UnselectGroup, UnselectSimilar, UserMenu, UuDecode, UuEncode    # manager.nml:18
from navigator.widgets.manager.commands import VerifyChecksums, View, ViewAsDataBase, ViewAsHex, ViewAsSpreadsheet    # manager.nml:19
from navigator.widgets.manager.commands import ViewAsText    # manager.nml:20
from navigator.widgets.shell.commands import InsertName, InsertPath, ToggleMarkBySpace    # manager.nml:21
from navml.widgets.dialog.commands import QuickSearch    # manager.nml:22
from navigator.widgets.tree.directory_tree import DirectoryTree    # manager.nml:23
from navigator.widgets.manager.info_panel import InfoPanel    # manager.nml:24
from navigator.widgets.manager.miller import MillerView    # manager.nml:25
from navigator.widgets.manager.panel import Panel    # manager.nml:26
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # manager.nml:27
from navml.widgets.menu.menu_item import MenuItem    # manager.nml:28
from navml.widgets.menu.menu_line import MenuLine    # manager.nml:29
from navml.widgets.menu.sub_menu import SubMenu    # manager.nml:30
from navml.widgets.window import Window    # manager.nml:31
from navigator.lib.file_ops.clip import CLIP    # manager.nml:32

__navml_component__ = "Manager"

__all__ = ["Manager"]


class Manager(Window, _Component):
    """The file manager: two panels, in a window on the desktop.

    DOS Navigator's ``TDoubleWindow``, and **frameless**: the two panels'
    frames are the window's frame, so there is nothing to draw around them.
    The close and zoom icons go on the panels' top edges and the resize grip on
    the right panel's corner, which ``Window.render_after`` paints over them.

    The panels share a row that is bound to the window's size, and the
    window's is not bound to anything: a drag assigns it, and the row
    re-arranges the panels because the size it reads is reactive.  Two panels
    that say nothing split it evenly, the odd column going to the right one.  The window opens zoomed, filling the desktop, which
    is what the desktop looked like before there was one.

    Where the two panels open is not here: a panel *navigates* its ``path``, and
    markup can only bind, so binding it would make ``enter()`` an error rather
    than a move.  The hand-written half seeds both instead -- see
    ``manager.py``.
    """

    #: The document this class was generated from.
    __navml_source__ = "manager.nml"

    #: The panel keys.  Up, down, the pages and Enter are not here: they move
    #: *within* a panel and are ``ListViewer``'s, reached first along the
    #: focus path.  What is here needs the window -- which panel, and what to
    #: do in it.  F2 to F8 are the key bar's panel half; every one without a
    #: handler in ``manager.py`` is disabled, and greyed on the bar.  The
    #: modified keys below them are the bar's Alt, Ctrl and Shift rows, in
    #: ``StatusDef hcFilePanel``'s order, which is the order the bar shows the
    #: letters in.  Three of DN's commands are not here, a departure: Ctrl+K's
    #: ``descript.ion`` descriptions, Shift+F3's modem phone book and Shift+F6's
    #: FAT undelete (*Reanimator*) can never mean anything on POSIX.  Some of
    #: DN's keys are others' here: Ctrl+K is Alternate edit, Shift+F6 Quick
    #: rename, Shift+F5 Make link (DN's *Split/Combine*, ``cmPanelLongCopy``, is
    #: File > Split/combine's alone), and Alt+I, DN's second (uncaptioned)
    #: ``cmDiskInfo``, the footer toggle (below).
    keys = {    # manager.nml:70
        'tab': SwitchPanel,    # manager.nml:71
        'space': ToggleMarkBySpace,    # manager.nml:72
        'ctrl+enter': InsertName,    # manager.nml:73
        'alt+enter': InsertName,    # manager.nml:74
        'ctrl+shift+enter': InsertPath,    # manager.nml:75
        'alt+shift+enter': InsertPath,    # manager.nml:76
        'f2': UserMenu,    # manager.nml:77
        'f3': View,# manager.nml:78
        'f4': Edit,# manager.nml:79
        'alt+f3': AlternateView,    # manager.nml:80
        'ctrl+k': AlternateEdit,    # manager.nml:83
        'alt+f4': AlternateEdit,    # manager.nml:84
        'f5': Copy,# manager.nml:85
        'f6': RenameMove,    # manager.nml:86
        'f7': MakeDirectory,    # manager.nml:87
        'f8': Delete,    # manager.nml:88
        'alt+b': SortBy,    # manager.nml:89
        'alt+c': ChangeDrive,    # manager.nml:90
        'alt+f1': ChangeLeft,    # manager.nml:93
        'alt+f2': ChangeRight,    # manager.nml:94
        'alt+shift+f1': ChangeLeft(focus=True),    # manager.nml:95
        'alt+shift+f2': ChangeRight(focus=True),    # manager.nml:96
        'alt+s': PanelSetup,    # manager.nml:97
        'alt+l': MakeList,    # manager.nml:98
        'alt+f6': FastRename,    # manager.nml:99
        'shift+f6': QuickRename,    # manager.nml:100
        'alt+f7': FindFile,    # manager.nml:101
        'alt+shift+f7': ReplaceInFiles,    # manager.nml:102
        'alt+r': Rescan,    # manager.nml:103
        'alt+t': ChangeDirectory,    # manager.nml:104
        'alt+e': ChangeAttributes,    # manager.nml:105
        'ctrl+f6': Calculator,    # manager.nml:106
        'ctrl+f9': PrintFile,    # manager.nml:107
        'ctrl+f7': UuEncode,    # manager.nml:108
        'ctrl+f8': UuDecode,    # manager.nml:109
        'ctrl+l': DiskInfo,    # manager.nml:110
        'ctrl+p': HideInactive,    # manager.nml:111
        'ctrl+u': SwapPanels,    # manager.nml:112
        'alt+f12': ToggleMiller,    # manager.nml:113
        'alt+=': EqualizePanels,    # manager.nml:114
        'alt+g': CountLength,    # manager.nml:115
        'shift+enter': EnterWithoutArchive,    # manager.nml:118
        'alt+v': ReadFileList,    # manager.nml:119
        'alt+y': Panelize,    # manager.nml:120
        'alt+a': MultiRename,    # manager.nml:121
        'alt+k': SetupColumns,    # manager.nml:122
        'alt+delete': AdvancedFilter,    # manager.nml:123
        'alt+backspace': DirHistory,    # manager.nml:124
        'alt+j': JumpToDirectory,    # manager.nml:125
        'ctrl+t': ToggleTree,    # manager.nml:126
        'ctrl+q': QuickView,    # manager.nml:127
        'ctrl+y': ToggleShowMode,    # manager.nml:128
        'ctrl+h': ToggleHidden,    # manager.nml:129
        'alt+i': ToggleInfoLines,    # manager.nml:134
        'ctrl+r': Rescan,    # manager.nml:135
        'ctrl+s': QuickSearch,    # manager.nml:136
        'shift+f1': ArchiveFiles,    # manager.nml:137
        'shift+f2': ExtractArchive,    # manager.nml:138
        'shift+f4': EditNamed,    # manager.nml:139
        'shift+f5': MakeLink,    # manager.nml:140
        'shift+f8': DeleteSingle,    # manager.nml:141
    }

    #: Ids, annotated so the hand-written half completes them.
    panels: HorizontalLayout    # manager.nml:269
    left: Panel    # manager.nml:277
    right: Panel    # manager.nml:281
    tree: DirectoryTree    # manager.nml:290
    info: InfoPanel    # manager.nml:298
    miller: MillerView    # manager.nml:303
    panel_menu: SubMenu    # manager.nml:320
    panel_display: SubMenu    # manager.nml:343
    panel_remember: SubMenu    # manager.nml:351
    panel_select: SubMenu    # manager.nml:363
    panel_other: SubMenu    # manager.nml:374

    #: The commands this component handles itself.
    async def on_toggle_miller(self, event: _Any) -> bool:    # manager.nml:145
        """``ToggleMiller``."""
        self.toggle_miller()
        return True

    async def on_hide_right(self, event: _Any) -> bool:    # manager.nml:146
        """``HideRight``."""
        await self.toggle_side('right')
        return True

    async def on_count_length(self, event: _Any) -> bool:    # manager.nml:147
        """``CountLength``."""
        self.spawn(self.count_length(self.active_panel))
        return True

    async def on_uu_encode(self, event: _Any) -> bool:    # manager.nml:148
        """``UuEncode``."""
        self.spawn(self.uu_encode(self.active_panel))
        return True

    async def on_uu_decode(self, event: _Any) -> bool:    # manager.nml:149
        """``UuDecode``."""
        self.spawn(self.uu_decode(self.active_panel))
        return True

    async def on_split_combine(self, event: _Any) -> bool:    # manager.nml:150
        """``SplitCombine``."""
        self.spawn(self.split_combine(self.active_panel))
        return True

    async def on_calculate_checksums(self, event: _Any) -> bool:    # manager.nml:151
        """``CalculateChecksums``."""
        self.spawn(self.calculate_checksums(self.active_panel))
        return True

    async def on_verify_checksums(self, event: _Any) -> bool:    # manager.nml:152
        """``VerifyChecksums``."""
        self.spawn(self.verify_checksums(self.active_panel))
        return True

    async def on_encrypt_files(self, event: _Any) -> bool:    # manager.nml:153
        """``EncryptFiles``."""
        self.spawn(self.encrypt_files(self.active_panel))
        return True

    async def on_decrypt_files(self, event: _Any) -> bool:    # manager.nml:154
        """``DecryptFiles``."""
        self.spawn(self.decrypt_files(self.active_panel))
        return True

    async def on_convert_text(self, event: _Any) -> bool:    # manager.nml:155
        """``ConvertText``."""
        self.spawn(self.convert_text(self.active_panel))
        return True

    async def on_extract_to(self, event: _Any) -> bool:    # manager.nml:156
        """``ExtractTo``."""
        self.spawn(self.extract_files(self.active_panel))
        return True

    async def on_arc_test(self, event: _Any) -> bool:    # manager.nml:157
        """``ArcTest``."""
        self.spawn(self.test_archive(self.active_panel))
        return True

    async def on_go_into(self, event: _Any) -> bool:    # manager.nml:158
        """``GoInto``."""
        self.active_panel.go_into()
        return True

    async def on_open_archive(self, event: _Any) -> bool:    # manager.nml:159
        """``OpenArchive``."""
        self.active_panel.open_as_archive()
        return True

    async def on_unmount_image(self, event: _Any) -> bool:    # manager.nml:160
        """``UnmountImage``."""
        self.spawn(self.unmount_image(self.active_panel))
        return True

    async def on_archive_files(self, event: _Any) -> bool:    # manager.nml:166
        """Shift+F1, File > Archive > *Create archive...*: ``cmPanelArcFiles``, DN's *Archive files* box (``ArchiveDialog``) naming the new archive and how it is packed, then a copy into it -- which makes it and packs it (``filecopy._open_target_archive``).  DN's caption was *Copy to archive*: renamed, a departure asked for, since it makes one."""
        self.spawn(self.archive_files(self.active_panel))
        return True

    async def on_go_to_file(self, event: _Any) -> bool:    # manager.nml:168
        """The right-click menu's *Go to file*: Enter in a *Find:* listing."""
        self.active_panel.go_to_entry()
        return True

    async def on_read_file_list(self, event: _Any) -> bool:    # manager.nml:169
        """``ReadFileList``."""
        self.spawn(self.read_file_list(self.active_panel))
        return True

    async def on_panelize(self, event: _Any) -> bool:    # manager.nml:170
        """``Panelize``."""
        self.spawn(self.panelize(self.active_panel))
        return True

    async def on_find_file(self, event: _Any) -> bool:    # manager.nml:171
        """``FindFile``."""
        self.spawn(self.find_file(self.active_panel))
        return True

    async def on_replace_in_files(self, event: _Any) -> bool:    # manager.nml:172
        """``ReplaceInFiles``."""
        self.spawn(self.replace_in_files(self.active_panel))
        return True

    async def on_dir_history(self, event: _Any) -> bool:    # manager.nml:173
        """``DirHistory``."""
        self.spawn(self.dir_history(self.active_panel))
        return True

    async def on_store_quick_dir(self, event: _Any) -> bool:    # manager.nml:174
        """``StoreQuickDir``."""
        self.spawn(self.store_quick_dir(self.active_panel, event.slot))
        return True

    async def on_list_of_dirs(self, event: _Any) -> bool:    # manager.nml:176
        """Alt+Shift+0: ``DoQuickChange``'s list, which is the bookmarks box."""
        self.spawn(self.choose_bookmark(self.active_panel))
        return True

    async def on_advanced_filter(self, event: _Any) -> bool:    # manager.nml:177
        """``AdvancedFilter``."""
        self.spawn(self.advanced_filter(self.active_panel))
        return True

    async def on_setup_columns(self, event: _Any) -> bool:    # manager.nml:178
        """``SetupColumns``."""
        self.spawn(self.setup_columns(self.active_panel))
        return True

    async def on_dir_branch(self, event: _Any) -> bool:    # manager.nml:179
        """``DirBranch``."""
        self.spawn(self.directory_branch(self.active_panel))
        return True

    async def on_find_duplicates(self, event: _Any) -> bool:    # manager.nml:180
        """``FindDuplicates``."""
        self.spawn(self.find_duplicates(self.active_panel))
        return True

    async def on_fast_rename(self, event: _Any) -> bool:    # manager.nml:181
        """``FastRename``."""
        self.spawn(self.fast_rename(self.active_panel))
        return True

    async def on_quick_rename(self, event: _Any) -> bool:    # manager.nml:182
        """``QuickRename``."""
        self.spawn(self.quick_rename(self.active_panel))
        return True

    async def on_multi_rename(self, event: _Any) -> bool:    # manager.nml:183
        """``MultiRename``."""
        self.spawn(self.multi_rename(self.active_panel))
        return True

    async def on_undo(self, event: _Any) -> bool:    # manager.nml:184
        """``Undo``."""
        self.spawn(self.undo(self.active_panel))
        return True

    async def on_restore_trash(self, event: _Any) -> bool:    # manager.nml:185
        """``RestoreTrash``."""
        self.spawn(self.restore_trash(self.active_panel))
        return True

    async def on_make_list(self, event: _Any) -> bool:    # manager.nml:186
        """``MakeList``."""
        self.spawn(self.make_list(self.active_panel))
        return True

    async def on_remember_directory(self, event: _Any) -> bool:    # manager.nml:187
        """``RememberDirectory``."""
        self.spawn(self.remember_directory(self.active_panel))
        return True

    async def on_remembered_directories(self, event: _Any) -> bool:    # manager.nml:188
        """``RememberedDirectories``."""
        self.spawn(self.remembered_directories(self.active_panel))
        return True

    async def on_panel_setup(self, event: _Any) -> bool:    # manager.nml:189
        """``PanelSetup``."""
        self.spawn(self.panel_setup(self.active_panel))
        return True

    async def on_compare_dir(self, event: _Any) -> bool:    # manager.nml:190
        """``CompareDir``."""
        self.spawn(self.compare_directories())
        return True

    async def on_diff_files(self, event: _Any) -> bool:    # manager.nml:191
        """``DiffFiles``."""
        self.spawn(self.diff_files())
        return True

    async def on_equalize_panels(self, event: _Any) -> bool:    # manager.nml:192
        """``EqualizePanels``."""
        self.equalize_panels()
        return True

    async def on_swap_panels(self, event: _Any) -> bool:    # manager.nml:193
        """``SwapPanels``."""
        self.swap_panels()
        return True

    async def on_hide_inactive(self, event: _Any) -> bool:    # manager.nml:194
        """``HideInactive``."""
        self.toggle_inactive_side()
        return True

    async def on_go_to_tree_directory(self, event: _Any) -> bool:    # manager.nml:195
        """``GoToTreeDirectory``."""
        await self.tree.choose()
        return True

    async def on_change_left(self, event: _Any) -> bool:    # manager.nml:196
        """``ChangeLeft``."""
        self.spawn(self._change_side('left', event.focus))
        return True

    async def on_change_right(self, event: _Any) -> bool:    # manager.nml:197
        """``ChangeRight``."""
        self.spawn(self._change_side('right', event.focus))
        return True

    async def on_change_drive(self, event: _Any) -> bool:    # manager.nml:198
        """``ChangeDrive``."""
        self.spawn(self.choose_bookmark(self.active_panel))
        return True

    async def on_scroll_names(self, event: _Any) -> bool:    # manager.nml:199
        """``ScrollNames``."""
        self.active_panel.scroll_names(event.step)
        return True

    async def on_select_similar(self, event: _Any) -> bool:    # manager.nml:200
        """``SelectSimilar``."""
        self.active_panel.select_similar(event.by, invert=event.invert)
        return True

    async def on_unselect_similar(self, event: _Any) -> bool:    # manager.nml:201
        """``UnselectSimilar``."""
        self.active_panel.select_similar(event.by, select=False, invert=event.invert)
        return True

    async def on_go_root(self, event: _Any) -> bool:    # manager.nml:202
        """``GoRoot``."""
        self.active_panel.go_root()
        return True

    async def on_toggle_mark(self, event: _Any) -> bool:    # manager.nml:204
        """Insert: tag the active panel's entry and step down."""
        self.active_panel.toggle_mark()
        return True

    async def on_invert_selection(self, event: _Any) -> bool:    # manager.nml:205
        """``InvertSelection``."""
        self.active_panel.invert_marks(directories=event.directories)
        return True

    async def on_select_all(self, event: _Any) -> bool:    # manager.nml:206
        """``SelectAll``."""
        self.active_panel.select_all()
        return True

    async def on_unselect_group(self, event: _Any) -> bool:    # manager.nml:207
        """``UnselectGroup``."""
        self.spawn(self.select_group(select=False, invert=event.invert))
        return True

    async def on_toggle_show_mode(self, event: _Any) -> bool:    # manager.nml:209
        """Ctrl+Y: the active panel's next show mode -- simple, detailed, list."""
        self.active_panel.cycle_view_mode()
        return True

    async def on_sort_by(self, event: _Any) -> bool:    # manager.nml:211
        """Alt+B: the active panel's order, chosen from a box (``CM_SortBy``)."""
        self.spawn(self.choose_sort(self.active_panel))
        return True

    async def on_toggle_hidden(self, event: _Any) -> bool:    # manager.nml:213
        """Ctrl+H: the active panel's dot-files, hidden or shown."""
        self.active_panel.toggle_hidden()
        return True

    async def on_toggle_info_lines(self, event: _Any) -> bool:    # manager.nml:215
        """Alt+I: the active panel's footer, hidden or shown."""
        self.active_panel.toggle_info()
        return True

    async def on_quick_search(self, event: _Any) -> bool:    # manager.nml:217
        """Ctrl+S: the active panel starts its quick search."""
        self.active_panel.start_quick_search()
        return True

    async def on_toggle_tree(self, event: _Any) -> bool:    # manager.nml:218
        """``ToggleTree``."""
        self.toggle_tree()
        return True

    async def on_quick_view(self, event: _Any) -> bool:    # manager.nml:219
        """``QuickView``."""
        self.toggle_quick_view()
        return True

    async def on_disk_info(self, event: _Any) -> bool:    # manager.nml:221
        """Ctrl+L: ``cmDiskInfo``, ``SwitchView(dtInfo)``."""
        self.switch_view(self.info)
        return True

    async def on_print_file(self, event: _Any) -> bool:    # manager.nml:223
        """Ctrl+F9: ``cmPrintFile``, DN's ``CM_Print`` -> ``PrintFiles`` (``GAUGES.PAS``)."""
        self.spawn(self.print_files())
        return True

    async def on_copy(self, event: _Any) -> bool:    # manager.nml:225
        """F5: ``cmCopyFiles``."""
        self.spawn(self.tree_copy(move=False) if self.tree.focused else self.copy_files(move=False))
        return True

    async def on_rename_move(self, event: _Any) -> bool:    # manager.nml:227
        """F6: ``cmMoveFiles``, the same dialog with *Remove source* ticked."""
        self.spawn(self.tree_copy(move=True) if self.tree.focused else self.copy_files(move=True))
        return True

    async def on_put_in_clipboard(self, event: _Any) -> bool:    # manager.nml:229
        """Ctrl+C, Ctrl+Ins: DN's ``_CtrlIns``, and the entries kept to copy."""
        self.clip_files(move=False)
        return True

    async def on_cut_to_clipboard(self, event: _Any) -> bool:    # manager.nml:231
        """Ctrl+X, Ctrl+Del: the same, kept to move."""
        self.clip_files(move=True)
        return True

    async def on_paste_from_clipboard(self, event: _Any) -> bool:    # manager.nml:233
        """Ctrl+V, Shift+Ins: what was clipped, into the active panel's directory."""
        self.spawn(self.paste_files())
        return True

    async def on_clear_clipboard(self, event: _Any) -> bool:    # manager.nml:234
        """``ClearClipboard``."""
        CLIP.clear()
        return True

    async def on_delete(self, event: _Any) -> bool:    # manager.nml:236
        """F8 and Del: ``cmPanelErase`` -- in the Ctrl+T tree, ``EraseDir``."""
        self.spawn(self.tree_erase() if self.tree.focused else self.delete_files(single=False))
        return True

    async def on_delete_single(self, event: _Any) -> bool:    # manager.nml:238
        """Shift+F8 and Shift+Del: ``cmSingleDel``, the cursor's entry whatever is tagged."""
        self.spawn(self.delete_files(single=True))
        return True

    async def on_make_link(self, event: _Any) -> bool:    # manager.nml:240
        """Shift+F5: a link -- symbolic or hard -- to each selected entry."""
        self.spawn(self.make_links())
        return True

    async def on_edit_link_target(self, event: _Any) -> bool:    # manager.nml:241
        """``EditLinkTarget``."""
        self.spawn(self.edit_link_targets())
        return True

    async def on_link_relative(self, event: _Any) -> bool:    # manager.nml:242
        """``LinkRelative``."""
        self.spawn(self.switch_links(relative=True))
        return True

    async def on_link_absolute(self, event: _Any) -> bool:    # manager.nml:243
        """``LinkAbsolute``."""
        self.spawn(self.switch_links(relative=False))
        return True

    async def on_select_broken_links(self, event: _Any) -> bool:    # manager.nml:244
        """``SelectBrokenLinks``."""
        self.select_broken_links(self.active_panel)
        return True

    async def on_select_bad_names(self, event: _Any) -> bool:    # manager.nml:245
        """``SelectBadNames``."""
        self.select_bad_names(self.active_panel)
        return True

    async def on_show_hard_links(self, event: _Any) -> bool:    # manager.nml:246
        """``ShowHardLinks``."""
        self.spawn(self.show_hard_links(self.active_panel))
        return True

    async def on_change_attributes(self, event: _Any) -> bool:    # manager.nml:248
        """Alt+E: ``cmSetFAttr``, the File Attributes dialog over the selection."""
        self.spawn(self.change_attributes())
        return True

    async def on_view(self, event: _Any) -> bool:    # manager.nml:254
        """F3: ``cmFileView``, the selected file in a viewer window.  Or, with *Internal viewer* off in System Setup, what ``viewers.ini`` says for it, else ``$PAGER`` on the console (:meth:`view_file`); and in hex from the start with the viewer's *Hex mode* on."""
        self.spawn(self.view_file(True))
        return True

    async def on_alternate_view(self, event: _Any) -> bool:    # manager.nml:256
        """Alt+F3, File > Alternate view: ``cmIntFileView``, F3 the other way round."""
        self.spawn(self.view_file(False))
        return True

    async def on_view_as_text(self, event: _Any) -> bool:    # manager.nml:257
        """``ViewAsText``."""
        self.spawn(self.view('text'))
        return True

    async def on_view_as_hex(self, event: _Any) -> bool:    # manager.nml:258
        """``ViewAsHex``."""
        self.spawn(self.view('hex'))
        return True

    async def on_view_as_data_base(self, event: _Any) -> bool:    # manager.nml:259
        """``ViewAsDataBase``."""
        self.spawn(self.view('database'))
        return True

    async def on_view_as_spreadsheet(self, event: _Any) -> bool:    # manager.nml:260
        """``ViewAsSpreadsheet``."""
        self.spawn(self.view('sheet'))
        return True

    async def on_alternate_edit(self, event: _Any) -> bool:    # manager.nml:264
        """Alt+F4, File > Alternate edit: ``cmIntFileEdit``, F4 the other way round -- with *Internal editor* on and nothing in ``editors.ini``, a console editor in a window (:meth:`console_editor`)."""
        self.spawn(self.edit_file(False))
        return True

    async def on_edit_named(self, event: _Any) -> bool:    # manager.nml:266
        """Shift+F4: ``cmXEditFile``, a file named in a dialog, new or not."""
        self.spawn(self.edit_named())
        return True

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_left_dropped(self, event: _Event) -> bool:    # manager.nml:277
        """``left`` raised an event whose handler is ``on_dropped``."""
        return False

    async def on_left_execute_file(self, event: _Event) -> bool:    # manager.nml:277
        """``left`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_left_open_file(self, event: _Event) -> bool:    # manager.nml:277
        """``left`` raised an event whose handler is ``on_open_file``."""
        return False

    async def on_right_dropped(self, event: _Event) -> bool:    # manager.nml:281
        """``right`` raised an event whose handler is ``on_dropped``."""
        return False

    async def on_right_execute_file(self, event: _Event) -> bool:    # manager.nml:281
        """``right`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_right_open_file(self, event: _Event) -> bool:    # manager.nml:281
        """``right`` raised an event whose handler is ``on_open_file``."""
        return False

    async def on_tree_chosen(self, event: _Event) -> bool:    # manager.nml:290
        """``tree`` raised an event whose handler is ``on_chosen``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.panels = HorizontalLayout(parent=self)    # manager.nml:268
        self.left = Panel(parent=self.panels)    # manager.nml:276
        self.right = Panel(parent=self.panels)    # manager.nml:280
        self.tree = DirectoryTree(parent=self.panels)    # manager.nml:289
        self.info = InfoPanel(parent=self.panels)    # manager.nml:297
        self.miller = MillerView(parent=self.panels)    # manager.nml:302
        self.panel_menu = SubMenu(parent=self)    # manager.nml:319
        _w1 = MenuItem(parent=self.panel_menu)    # manager.nml:322
        _w2 = MenuItem(parent=self.panel_menu)    # manager.nml:324
        _w3 = MenuItem(parent=self.panel_menu)    # manager.nml:327
        _w4 = MenuItem(parent=self.panel_menu)    # manager.nml:329
        _w5 = MenuItem(parent=self.panel_menu)    # manager.nml:331
        _w6 = MenuItem(parent=self.panel_menu)    # manager.nml:333
        _w7 = MenuItem(parent=self.panel_menu)    # manager.nml:336
        _w8 = MenuLine(parent=self.panel_menu)    # manager.nml:338
        _w9 = MenuItem(parent=self.panel_menu)    # manager.nml:339
        _w10 = MenuItem(parent=self.panel_menu)    # manager.nml:340
        _w11 = MenuItem(parent=self.panel_menu)    # manager.nml:341
        self.panel_display = SubMenu(parent=self.panel_menu)    # manager.nml:342
        _w12 = MenuItem(parent=self.panel_display)    # manager.nml:345
        _w13 = MenuItem(parent=self.panel_display)    # manager.nml:346
        _w14 = MenuItem(parent=self.panel_display)    # manager.nml:347
        self.panel_remember = SubMenu(parent=self.panel_display)    # manager.nml:350
        _w15 = MenuItem(parent=self.panel_remember)    # manager.nml:353
        _w16 = MenuItem(parent=self.panel_remember)    # manager.nml:355
        _w17 = MenuLine(parent=self.panel_display)    # manager.nml:357
        _w18 = MenuItem(parent=self.panel_display)    # manager.nml:360
        _w19 = MenuItem(parent=self.panel_display)    # manager.nml:361
        self.panel_select = SubMenu(parent=self.panel_menu)    # manager.nml:362
        _w20 = MenuItem(parent=self.panel_select)    # manager.nml:365
        _w21 = MenuItem(parent=self.panel_select)    # manager.nml:366
        _w22 = MenuItem(parent=self.panel_select)    # manager.nml:367
        _w23 = MenuItem(parent=self.panel_select)    # manager.nml:368
        _w24 = MenuLine(parent=self.panel_select)    # manager.nml:370
        _w25 = MenuItem(parent=self.panel_select)    # manager.nml:371
        self.panel_other = SubMenu(parent=self.panel_menu)    # manager.nml:373
        _w26 = MenuItem(parent=self.panel_other)    # manager.nml:376
        _w27 = MenuItem(parent=self.panel_other)    # manager.nml:377
        _w28 = MenuItem(parent=self.panel_other)    # manager.nml:379
        _w29 = MenuLine(parent=self.panel_other)    # manager.nml:381
        _w30 = MenuItem(parent=self.panel_other)    # manager.nml:382
        _w31 = MenuItem(parent=self.panel_other)    # manager.nml:388
        _w32 = MenuLine(parent=self.panel_menu)    # manager.nml:390
        _w33 = MenuItem(parent=self.panel_menu)    # manager.nml:391
        _w34 = MenuItem(parent=self.panel_menu)    # manager.nml:393
        _w35 = MenuItem(parent=self.panel_menu)    # manager.nml:396
        _w36 = MenuItem(parent=self.panel_menu)    # manager.nml:398
        _w37 = MenuItem(parent=self.panel_menu)    # manager.nml:399
        _w38 = MenuItem(parent=self.panel_menu)    # manager.nml:400
        _w39 = MenuItem(parent=self.panel_menu)    # manager.nml:402

        self.zoomed = True    # manager.nml:52
        self.min_width = 24    # manager.nml:53
        self.min_height = 5    # manager.nml:54

        self.panels.x = 0    # manager.nml:271
        self.panels.width = _bind(lambda _o: max(0, _o.parent.width))    # manager.nml:272
        self.panels.y = 0    # manager.nml:273
        self.panels.height = _bind(lambda _o: max(0, _o.parent.height))    # manager.nml:274

        self.left.title_margin = 5    # manager.nml:278
        self.left.on_dropped = self.on_left_dropped    # manager.nml:277
        self.left.on_execute_file = self.on_left_execute_file    # manager.nml:277
        self.left.on_open_file = self.on_left_open_file    # manager.nml:277

        self.right.title_margin = 5    # manager.nml:282
        self.right.on_dropped = self.on_right_dropped    # manager.nml:281
        self.right.on_execute_file = self.on_right_execute_file    # manager.nml:281
        self.right.on_open_file = self.on_right_open_file    # manager.nml:281

        self.tree.type_to_search = False    # manager.nml:291
        self.tree.on_chosen = self.on_tree_chosen    # manager.nml:290

        self.panel_menu.text = _bind(lambda _o: _tr('~P~anel'), yielding=True)    # manager.nml:319
        self.panel_menu.after = 'Utilities'    # manager.nml:319
        self.panel_menu.tooltip = _bind(    # manager.nml:321
            lambda _o: _tr('List files, compare, sort, filter, select and change directory'),
            yielding=True,
        )

        _w1.text = _bind(lambda _o: _tr('~M~ake list file...'), yielding=True)    # manager.nml:322
        _w1.command = MakeList    # manager.nml:322
        _w1.key = 'Alt-L'    # manager.nml:322
        _w1.tooltip = _bind(    # manager.nml:323
            lambda _o: _tr("Write the tagged files' names to a list file"),
            yielding=True,
        )

        _w2.text = _bind(lambda _o: _tr('Read file ~l~ist'), yielding=True)    # manager.nml:324
        _w2.command = ReadFileList    # manager.nml:324
        _w2.key = 'Alt-V'    # manager.nml:324
        _w2.tooltip = _bind(    # manager.nml:325
            lambda _o: _tr('Show the files a list file names as a listing'),
            yielding=True,
        )

        _w3.text = _bind(    # manager.nml:327
            lambda _o: _tr('Paneli~z~e command...'),
            yielding=True,
        )
        _w3.command = Panelize    # manager.nml:327
        _w3.key = 'Alt-Y'    # manager.nml:327
        _w3.tooltip = _bind(    # manager.nml:328
            lambda _o: _tr('Run a command and list the files it prints in the panel'),
            yielding=True,
        )

        _w4.text = _bind(    # manager.nml:329
            lambda _o: _tr('~C~ompare directories'),
            yielding=True,
        )
        _w4.command = CompareDir    # manager.nml:329
        _w4.tooltip = _bind(    # manager.nml:330
            lambda _o: _tr('Tag what each panel has that the other lacks or has older'),
            yielding=True,
        )

        _w5.text = _bind(    # manager.nml:331
            lambda _o: _tr('Count directory len~g~th'),
            yielding=True,
        )
        _w5.command = CountLength    # manager.nml:331
        _w5.key = 'Alt-G'    # manager.nml:331
        _w5.tooltip = _bind(    # manager.nml:332
            lambda _o: _tr('Add up the bytes under the selected directories'),
            yielding=True,
        )

        _w6.text = _bind(lambda _o: _tr('Directory Branc~h~'), yielding=True)    # manager.nml:333
        _w6.command = DirBranch    # manager.nml:333
        _w6.tooltip = _bind(    # manager.nml:334
            lambda _o: _tr('Every file below this directory in one listing'),
            yielding=True,
        )

        _w7.text = _bind(lambda _o: _tr('Find duplicates...'), yielding=True)    # manager.nml:336
        _w7.command = FindDuplicates    # manager.nml:336
        _w7.tooltip = _bind(    # manager.nml:337
            lambda _o: _tr('List the files below this directory whose contents are the same'),
            yielding=True,
        )

        _w9.text = _bind(lambda _o: _tr('Setup c~o~lumns'), yielding=True)    # manager.nml:339
        _w9.command = SetupColumns    # manager.nml:339
        _w9.key = 'Alt-K'    # manager.nml:339

        _w10.text = _bind(lambda _o: _tr('~S~etup Panel'), yielding=True)    # manager.nml:340
        _w10.command = PanelSetup    # manager.nml:340
        _w10.key = 'Alt-S'    # manager.nml:340

        _w11.text = _bind(lambda _o: _tr('Sort ~b~y...'), yielding=True)    # manager.nml:341
        _w11.command = SortBy    # manager.nml:341
        _w11.key = 'Alt-B'    # manager.nml:341

        self.panel_display.text = _bind(    # manager.nml:342
            lambda _o: _tr('D~i~splay'),
            yielding=True,
        )
        self.panel_display.tooltip = _bind(    # manager.nml:344
            lambda _o: _tr('View mode, hidden files, the footer, directory settings and the divider'),
            yielding=True,
        )

        _w12.text = _bind(lambda _o: _tr('Vie~w~ mode'), yielding=True)    # manager.nml:345
        _w12.command = ToggleShowMode    # manager.nml:345
        _w12.key = 'Ctrl-Y'    # manager.nml:345

        _w13.text = _bind(    # manager.nml:346
            lambda _o: _tr('Show/hide h~i~dden files'),
            yielding=True,
        )
        _w13.command = ToggleHidden    # manager.nml:346
        _w13.key = 'Ctrl-H'    # manager.nml:346

        _w14.text = _bind(lambda _o: _tr('Show/hide ~f~ooter'), yielding=True)    # manager.nml:347
        _w14.command = ToggleInfoLines    # manager.nml:347
        _w14.key = 'Alt-I'    # manager.nml:347

        self.panel_remember.text = _bind(    # manager.nml:350
            lambda _o: _tr('Director~y~ settings'),
            yielding=True,
        )
        self.panel_remember.tooltip = _bind(    # manager.nml:352
            lambda _o: _tr('Remember the sort order, view and file mask for a directory, and the list of those remembered'),
            yielding=True,
        )

        _w15.text = _bind(    # manager.nml:353
            lambda _o: _tr('Remember ~f~or this directory'),
            yielding=True,
        )
        _w15.command = RememberDirectory    # manager.nml:353
        _w15.tooltip = _bind(    # manager.nml:354
            lambda _o: _tr('Keep the sort order, view, columns and file mask shown for this directory'),
            yielding=True,
        )

        _w16.text = _bind(    # manager.nml:355
            lambda _o: _tr('Remembered director~y~ list...'),
            yielding=True,
        )
        _w16.command = RememberedDirectories    # manager.nml:355
        _w16.tooltip = _bind(    # manager.nml:356
            lambda _o: _tr('The directories with settings of their own: go to one, or forget it'),
            yielding=True,
        )

        _w18.text = _bind(lambda _o: _tr('Move divider left'), yielding=True)    # manager.nml:360
        _w18.command = MoveSeparator(step=-1)    # manager.nml:360
        _w18.key = 'Alt-Left'    # manager.nml:360

        _w19.text = _bind(lambda _o: _tr('Move divider right'), yielding=True)    # manager.nml:361
        _w19.command = MoveSeparator(step=1)    # manager.nml:361
        _w19.key = 'Alt-Right'    # manager.nml:361

        self.panel_select.text = _bind(    # manager.nml:362
            lambda _o: _tr('Selectio~n~'),
            yielding=True,
        )
        self.panel_select.tooltip = _bind(    # manager.nml:364
            lambda _o: _tr('Select or unselect files by a mask, or filter them'),
            yielding=True,
        )

        _w20.text = _bind(lambda _o: _tr('Select grou~p~...'), yielding=True)    # manager.nml:365
        _w20.command = SelectGroup    # manager.nml:365
        _w20.key = 'Gray "+"'    # manager.nml:365

        _w21.text = _bind(lambda _o: _tr('~U~nselect group...'), yielding=True)    # manager.nml:366
        _w21.command = UnselectGroup    # manager.nml:366
        _w21.key = 'Gray "-"'    # manager.nml:366

        _w22.text = _bind(lambda _o: _tr('In~v~ert selection'), yielding=True)    # manager.nml:367
        _w22.command = InvertSelection    # manager.nml:367
        _w22.key = 'Gray "*"'    # manager.nml:367

        _w23.text = _bind(lambda _o: _tr('Select all files'), yielding=True)    # manager.nml:368
        _w23.command = SelectAll    # manager.nml:368
        _w23.key = 'Ctrl-A'    # manager.nml:368
        _w23.tooltip = _bind(    # manager.nml:369
            lambda _o: _tr('Select every file and directory in this panel'),
            yielding=True,
        )

        _w25.text = _bind(lambda _o: _tr('Advanced filter...'), yielding=True)    # manager.nml:371
        _w25.command = AdvancedFilter    # manager.nml:371
        _w25.key = 'Alt-Del'    # manager.nml:371
        _w25.tooltip = _bind(    # manager.nml:372
            lambda _o: _tr('Show or hide files by extension'),
            yielding=True,
        )

        self.panel_other.text = _bind(    # manager.nml:373
            lambda _o: _tr('Other ~p~anel'),
            yielding=True,
        )
        self.panel_other.tooltip = _bind(    # manager.nml:375
            lambda _o: _tr('Put a tree, information or a preview in the other panel'),
            yielding=True,
        )

        _w26.text = _bind(lambda _o: _tr('Director~y~ tree'), yielding=True)    # manager.nml:376
        _w26.command = ToggleTree    # manager.nml:376
        _w26.key = 'Ctrl-T'    # manager.nml:376

        _w27.text = _bind(lambda _o: _tr('I~n~fo'), yielding=True)    # manager.nml:377
        _w27.command = DiskInfo    # manager.nml:377
        _w27.key = 'Ctrl-L'    # manager.nml:377
        _w27.tooltip = _bind(    # manager.nml:378
            lambda _o: _tr('Disk and directory information in the other panel'),
            yielding=True,
        )

        _w28.text = _bind(lambda _o: _tr('Quic~k~ view'), yielding=True)    # manager.nml:379
        _w28.command = QuickView    # manager.nml:379
        _w28.key = 'Ctrl-Q'    # manager.nml:379
        _w28.tooltip = _bind(    # manager.nml:380
            lambda _o: _tr('Preview the file at the cursor in the other panel'),
            yielding=True,
        )

        _w30.text = _bind(    # manager.nml:382
            lambda _o: _tr('S~a~me directory in other panel'),
            yielding=True,
        )
        _w30.command = EqualizePanels    # manager.nml:382
        _w30.key = 'Alt-='    # manager.nml:382
        _w30.tooltip = _bind(    # manager.nml:383
            lambda _o: _tr('Send the other panel to this directory'),
            yielding=True,
        )

        _w31.text = _bind(lambda _o: _tr('Show in other panel'), yielding=True)    # manager.nml:388
        _w31.command = ChangeInactive    # manager.nml:388
        _w31.key = 'Shift-Enter'    # manager.nml:388
        _w31.tooltip = _bind(    # manager.nml:389
            lambda _o: _tr('Show the found file in the other panel'),
            yielding=True,
        )

        _w33.text = _bind(lambda _o: _tr('Change ~d~rive'), yielding=True)    # manager.nml:391
        _w33.command = ChangeDrive    # manager.nml:391
        _w33.key = 'Alt-C'    # manager.nml:391
        _w33.tooltip = _bind(    # manager.nml:392
            lambda _o: _tr('Send this panel to a bookmarked directory'),
            yielding=True,
        )

        _w34.text = _bind(lambda _o: _tr('Change direc~t~ory'), yielding=True)    # manager.nml:393
        _w34.command = ChangeDirectory    # manager.nml:393
        _w34.key = 'Alt-T'    # manager.nml:393
        _w34.tooltip = _bind(    # manager.nml:394
            lambda _o: _tr('Choose a directory from a tree'),
            yielding=True,
        )

        _w35.text = _bind(    # manager.nml:396
            lambda _o: _tr('~J~ump to directory...'),
            yielding=True,
        )
        _w35.command = JumpToDirectory    # manager.nml:396
        _w35.key = 'Alt-J'    # manager.nml:396
        _w35.tooltip = _bind(    # manager.nml:397
            lambda _o: _tr("zoxide's directories and the panels' history, searched by fzf"),
            yielding=True,
        )

        _w36.text = _bind(lambda _o: _tr('Quick s~e~arch'), yielding=True)    # manager.nml:398
        _w36.command = QuickSearch    # manager.nml:398
        _w36.key = 'Ctrl-S'    # manager.nml:398

        _w37.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # manager.nml:399
        _w37.command = Rescan    # manager.nml:399
        _w37.key = 'Alt-R'    # manager.nml:399

        _w38.text = _bind(lambda _o: _tr('~Q~uick dirs...'), yielding=True)    # manager.nml:400
        _w38.command = ListOfDirs    # manager.nml:400
        _w38.key = 'Alt-Shift-0'    # manager.nml:400
        _w38.tooltip = _bind(    # manager.nml:401
            lambda _o: _tr('The bookmarks, for this panel'),
            yielding=True,
        )

        _w39.text = _bind(    # manager.nml:402
            lambda _o: _tr('History of directories...'),
            yielding=True,
        )
        _w39.command = DirHistory    # manager.nml:402
        _w39.key = 'Alt-BkSp'    # manager.nml:402

        self._navml_built(__class__)
