"""Modal screens used by the second_brain TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class ConfirmModal(ModalScreen[bool]):
    """Yes/No confirmation dialog. Returns ``True`` on confirm."""

    BINDINGS = [
        ("escape", "dismiss(False)", "Cancel"),
        ("y", "dismiss(True)", "Confirm"),
        ("n", "dismiss(False)", "Cancel"),
    ]

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Label(self._message, id="confirm-msg")
            yield Button("Yes (y)", id="confirm-yes", variant="error")
            yield Button("No (n)", id="confirm-no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-yes")


class NewNoteModal(ModalScreen[str | None]):
    """Prompt for a new note body. Returns the entered text, or ``None``."""

    BINDINGS = [("escape", "dismiss(None)", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="new-note-box"):
            yield Label("New note (Enter to save, Esc to cancel):")
            yield Input(placeholder="Type your thought…", id="new-note-input")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        self.dismiss(text or None)
