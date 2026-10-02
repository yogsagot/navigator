"""The setup dialogs under Options: one per section of ``navigator.ini``.

System Setup, Startup, Interface, Confirmations and Editor/Viewer from
Options > Configuration, and Setup and New Manager defaults from Options >
File Manager -- DOS Navigator's ``dlgSystemSetup``, ``dlgStartupSetup``,
``dlgInterfaceSetup``, ``dlgConfirmations``, ``dlgEditorDefaults``,
``dlgFMSetup`` and ``dlgFMDefaults``.  Each is seeded from its
:mod:`navigator.settings` section and accepts a dict of new values for it;
``Shell`` assigns and saves them.

A **group**, not a component -- see *Components come in groups* in
``navml/DESIGN.md``.  This file imports none of its members.
"""
