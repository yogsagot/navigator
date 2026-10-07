"""What *Setup game* opens on and answers: ``TetrisRec``, with the level the
game has reached as DN put it (``TetrisRec.L := Level - 1``)."""

from __future__ import annotations

from typing import Any

from navkit.events import Event

from navml.widgets.dialog.dialog import Dialog

from navigator.settings import SETTINGS, TetrisData


class GameSetupDialog(Dialog):
    """The level a game starts at, Tetris or Pentix, and the preview."""

    def __init__(self, level: int | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        setup = SETTINGS.tetris
        self.level.value = self.level.sel = max(1, min(10, level or setup.level)) - 1
        self.game_style.value = self.game_style.sel = TetrisData.STYLES.index(setup.style)
        self.options.value = 1 if setup.preview else 0

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon)

    def accept(self) -> dict[str, Any]:
        return {"level": self.level.value + 1, "style": TetrisData.STYLES[self.game_style.value],
                "preview": bool(self.options.value & 1)}

    async def on_pick_click(self, event: Event) -> bool:
        self.close(self.accept())
        return True
