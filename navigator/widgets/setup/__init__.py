"""The setup dialogs under Options, and the pages of *Settings*.

Options > Settings (``settings_dialog``) holds one page per section of
``navigator.ini`` behind a row of tabs: System Setup, Startup, Interface,
Confirmations, Screen savers and Editor/Viewer from Options > Configuration,
and Setup, Information panel, New Manager defaults, Column defaults and
Highlight groups from Options > File Manager -- DOS Navigator's
``dlgSystemSetup``, ``dlgStartupSetup``, ``dlgInterfaceSetup``,
``dlgConfirmations``, ``TSaversDialog``, ``dlgEditorDefaults``, ``dlgFMSetup``,
``dlgDriveInfoSetup``, ``dlgFMDefaults``, ``dlgColumnsDefaults`` and
``dlgHighlightGroups``, each a dialog of its own there.  Each page
(``*_page``) is seeded from its :mod:`navigator.settings` section and accepts
a dict of new values for it; ``Shell`` assigns and saves the sections that
changed.  Colors and Key bindings stay dialogs of their own.

A **group**, not a component -- see *Components come in groups* in
``navml/DESIGN.md``.  This file imports none of its members.
"""
