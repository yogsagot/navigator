"""The game window's commands: ``StatusDef hcTetris``'s keys."""

from __future__ import annotations

from navkit.commands import Command


class NewGame(Command):
    """F2, Alt+N, *New*: ``cmNewGame``."""

    title = "New game"


class PauseGame(Command):
    """F3, Alt+P, *Pause*: ``cmStop``."""

    title = "Pause"


class ShowTopTen(Command):
    """F4, Alt+T, *Top 10*: ``cmShowHi``."""

    title = "Top 10"


class GameSetup(Command):
    """F5, Alt+S, *Setup*: ``cmSetup``."""

    title = "Setup"


class LevelUp(Command):
    """Gray +: ``cmTetrisIncLevel``."""

    title = "Level"


class TogglePreview(Command):
    """Gray *: ``cmTetrisPreview``."""

    title = "Preview"


__all__ = ["NewGame", "PauseGame", "ShowTopTen", "GameSetup", "LevelUp", "TogglePreview"]
