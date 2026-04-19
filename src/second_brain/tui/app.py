"""Textual application for browsing and editing second_brain notes."""

from __future__ import annotations

import os
import shlex
import subprocess
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Footer,
    Header,
    Input,
    ListItem,
    ListView,
    Markdown,
    Static,
)

from second_brain.notes import (
    NoteEntry,
    delete_note,
    filter_notes,
    iter_notes,
    resolve_storage_dir,
    save_thought,
)
from second_brain.tui.modals import ConfirmModal, NewNoteModal


class SecondBrainApp(App[None]):
    """Interactive browser for markdown notes under ``$SB_DIR``."""

    CSS = """
    Screen { layout: vertical; }
    #main { height: 1fr; }
    #sidebar { width: 48; border-right: tall $accent; }
    #preview { border: tall $accent; padding: 0 1; }
    #search { dock: top; }
    #confirm-box, #new-note-box {
        width: 60%;
        padding: 1 2;
        background: $panel;
        border: thick $accent;
    }
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("slash", "focus_search", "Search"),
        Binding("escape", "blur_search", "Blur", show=False),
        Binding("enter", "open_selected", "Preview", show=False),
        Binding("e", "edit_selected", "Edit"),
        Binding("d", "delete_selected", "Delete"),
        Binding("n", "new_note", "New"),
        Binding("r", "refresh_notes", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, storage_dir: Path | None = None) -> None:
        super().__init__()
        self.storage_dir = storage_dir or resolve_storage_dir()
        self._entries: list[NoteEntry] = []
        self._visible: list[NoteEntry] = []
        self._suppress_highlight = False

    # -- layout -------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="main"):
            with Vertical(id="sidebar"):
                yield Input(placeholder="/ search", id="search")
                yield ListView(id="notes")
            yield Markdown("Select a note to preview.", id="preview")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "second_brain"
        self.sub_title = str(self.storage_dir)
        self.action_refresh_notes()

    # -- data ---------------------------------------------------------------

    def _reload_list(self, query: str = "") -> None:
        self._visible = filter_notes(self._entries, query)
        list_view = self.query_one("#notes", ListView)
        self._suppress_highlight = True
        try:
            list_view.clear()
            for entry in self._visible:
                date = datetime.fromtimestamp(entry.mtime).strftime("%Y-%m-%d %H:%M")
                label = f"{entry.title} — {entry.first_line} — {date}"
                list_view.append(ListItem(Static(label)))
            if self._visible:
                list_view.index = 0
            else:
                self.query_one("#preview", Markdown).update("_No notes match._")
        finally:
            self._suppress_highlight = False
        if self._visible:
            self._show_preview(self._visible[0])

    def _show_preview(self, entry: NoteEntry) -> None:
        try:
            body = entry.path.read_text(encoding="utf-8")
        except OSError as exc:
            body = f"_Could not read note: {exc}_"
        self.query_one("#preview", Markdown).update(body)

    def _selected(self) -> NoteEntry | None:
        list_view = self.query_one("#notes", ListView)
        idx = list_view.index
        if idx is None or idx < 0 or idx >= len(self._visible):
            return None
        return self._visible[idx]

    # -- actions ------------------------------------------------------------

    def action_refresh_notes(self) -> None:
        self._entries = iter_notes(self.storage_dir)
        query = self.query_one("#search", Input).value
        self._reload_list(query)

    def action_focus_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_blur_search(self) -> None:
        self.query_one("#notes", ListView).focus()

    def action_cursor_down(self) -> None:
        self.query_one("#notes", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#notes", ListView).action_cursor_up()

    def action_open_selected(self) -> None:
        entry = self._selected()
        if entry is not None:
            self._show_preview(entry)

    def action_new_note(self) -> None:
        def _on_submit(text: str | None) -> None:
            if not text:
                return
            save_thought(text, self.storage_dir)
            self.action_refresh_notes()

        self.push_screen(NewNoteModal(), _on_submit)

    def action_delete_selected(self) -> None:
        entry = self._selected()
        if entry is None:
            return

        def _on_confirm(confirmed: bool | None) -> None:
            if not confirmed:
                return
            try:
                delete_note(entry)
            except FileNotFoundError:
                self.notify(f"'{entry.title}' was already gone.", severity="warning")
            self.action_refresh_notes()

        self.push_screen(ConfirmModal(f"Delete '{entry.title}'? (y/n)"), _on_confirm)

    def action_edit_selected(self) -> None:
        entry = self._selected()
        if entry is None:
            return
        editor = os.environ.get("EDITOR", "vi")
        argv = shlex.split(editor) + [str(entry.path)]
        with self.suspend():
            subprocess.run(argv, check=False)
        self.action_refresh_notes()

    # -- events -------------------------------------------------------------

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search":
            self._reload_list(event.value)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if self._suppress_highlight:
            return
        entry = self._selected()
        if entry is not None:
            self._show_preview(entry)


def run() -> None:
    """Launch the interactive TUI."""
    SecondBrainApp().run()
