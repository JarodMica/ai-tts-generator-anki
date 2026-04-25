from __future__ import annotations

import html
import re
from dataclasses import replace

from aqt import mw
from aqt.qt import (
    QAbstractItemView,
    QComboBox,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    Qt,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import qconnect, showInfo, showWarning

from .config import (
    AddonConfig,
    EndpointConfig,
    HeaderConfig,
    MappingConfig,
    import_asset,
    load_config,
    save_config,
)
from .constants import USER_FILES_DIR
from .version import APP_VERSION


class WrappingPathLabel(QLabel):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__("", parent)
        self._raw_text = text
        self.setWordWrap(True)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        self.setMinimumWidth(0)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._apply_wrapped_text()

    def minimumSizeHint(self):
        hint = super().minimumSizeHint()
        hint.setWidth(0)
        return hint

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setWidth(0)
        return hint

    def set_path_text(self, text: str) -> None:
        self._raw_text = text
        self.setToolTip("" if text == "Not configured" else text)
        self._apply_wrapped_text()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_wrapped_text()

    def _apply_wrapped_text(self) -> None:
        if self._raw_text == "Not configured":
            super().setText("Not configured")
            return
        super().setText(self._wrap_path_to_width(self._raw_text, self.width()))

    def _wrap_path_to_width(self, value: str, width: int) -> str:
        metrics = self.fontMetrics()
        available = max(120, width - 8)
        tokens = self._tokenize_path(value)
        lines: list[str] = []
        current = ""

        for token in tokens:
            candidate = f"{current}{token}"
            if current and metrics.horizontalAdvance(candidate) > available:
                lines.append(current)
                current = token
            else:
                current = candidate

        if current:
            lines.append(current)

        return "<br>".join(html.escape(line) for line in lines if line)

    def _tokenize_path(self, value: str) -> list[str]:
        primary_parts = re.split(r"([\\/])", value)
        tokens: list[str] = []
        for part in primary_parts:
            if not part:
                continue
            if part in ("\\", "/"):
                if tokens:
                    tokens[-1] = f"{tokens[-1]}{part}"
                else:
                    tokens.append(part)
                continue

            secondary_parts = re.split(r"([_.-])", part)
            current = ""
            for piece in secondary_parts:
                if not piece:
                    continue
                current += piece
                if piece in ("_", ".", "-"):
                    tokens.append(current)
                    current = ""
            if current:
                tokens.append(current)
        return tokens


class MappingEditorDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        mapping: MappingConfig | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Deck and Note Type Mapping")
        self.setModal(True)
        self._mapping = mapping

        self.deck_combo = QComboBox(self)
        self.note_type_combo = QComboBox(self)
        self.source_field_combo = QComboBox(self)
        self.target_field_combo = QComboBox(self)

        for deck in mw.col.decks.all_names_and_ids(include_filtered=False):
            self.deck_combo.addItem(deck.name)
        for notetype in mw.col.models.all_names_and_ids():
            self.note_type_combo.addItem(notetype.name)

        qconnect(self.note_type_combo.currentTextChanged, self._reload_field_combos)

        form = QFormLayout()
        form.addRow("Deck", self.deck_combo)
        form.addRow("Note type", self.note_type_combo)
        form.addRow("Source field", self.source_field_combo)
        form.addRow("Target audio field", self.target_field_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        qconnect(buttons.accepted, self.accept)
        qconnect(buttons.rejected, self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if mapping:
            self.deck_combo.setCurrentText(mapping.deck_name)
            self.note_type_combo.setCurrentText(mapping.note_type_name)
        self._reload_field_combos()
        if mapping:
            self.source_field_combo.setCurrentText(mapping.source_field)
            self.target_field_combo.setCurrentText(mapping.target_field)

    def _reload_field_combos(self) -> None:
        self.source_field_combo.clear()
        self.target_field_combo.clear()
        note_type_name = self.note_type_combo.currentText()
        notetype_id = mw.col.models.id_for_name(note_type_name)
        if not notetype_id:
            return
        notetype = mw.col.models.get(notetype_id)
        if not notetype:
            return
        field_names = mw.col.models.field_names(notetype)
        self.source_field_combo.addItems(field_names)
        self.target_field_combo.addItems(field_names)

    def mapping(self) -> MappingConfig:
        return MappingConfig(
            deck_name=self.deck_combo.currentText().strip(),
            note_type_name=self.note_type_combo.currentText().strip(),
            source_field=self.source_field_combo.currentText().strip(),
            target_field=self.target_field_combo.currentText().strip(),
        )

    def accept(self) -> None:
        mapping = self.mapping()
        if not all(
            [
                mapping.deck_name,
                mapping.note_type_name,
                mapping.source_field,
                mapping.target_field,
            ]
        ):
            showWarning("Every mapping needs a deck, note type, source field, and target field.")
            return
        super().accept()


class HeaderEditorDialog(QDialog):
    def __init__(self, parent: QWidget, header: HeaderConfig | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("HTTP Header")
        self.setModal(True)

        self.name_edit = QLineEdit(self)
        self.value_edit = QLineEdit(self)
        if header:
            self.name_edit.setText(header.name)
            self.value_edit.setText(header.value)

        form = QFormLayout()
        form.addRow("Header name", self.name_edit)
        form.addRow("Header value", self.value_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        qconnect(buttons.accepted, self.accept)
        qconnect(buttons.rejected, self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def header(self) -> HeaderConfig:
        return HeaderConfig(
            name=self.name_edit.text().strip(),
            value=self.value_edit.text(),
        )

    def accept(self) -> None:
        if not self.name_edit.text().strip():
            showWarning("Header name cannot be empty.")
            return
        super().accept()


class ConfigDialog(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Sentence Audio Generator (AI TTS) Settings v{APP_VERSION}")
        self.setModal(True)

        self.config = load_config()
        self.mappings = list(self.config.mappings)
        self.headers = list(self.config.headers)
        self.reference_source_path = ""
        self.transcript_source_path = ""

        self.host_edit = QLineEdit(self.config.endpoint.host, self)
        self.port_spin = QSpinBox(self)
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(self.config.endpoint.port)
        self.path_edit = QLineEdit(self.config.endpoint.path, self)
        self.timeout_spin = QSpinBox(self)
        self.timeout_spin.setRange(5, 600)
        self.timeout_spin.setValue(self.config.endpoint.timeout_seconds)
        self.text_field_edit = QLineEdit(self.config.endpoint.text_field_name, self)
        self.reference_audio_field_edit = QLineEdit(
            self.config.endpoint.reference_audio_field_name,
            self,
        )
        self.transcript_field_edit = QLineEdit(
            self.config.endpoint.transcript_text_field_name,
            self,
        )
        self.overwrite_tts_checkbox = QCheckBox(
            "Allow overwriting existing generated TTS audio",
            self,
        )
        self.overwrite_tts_checkbox.setChecked(
            self.config.overwrite_existing_tts_audio
        )
        self.overwrite_tts_note = QLabel(
            "Only applies when the target field contains sound tags and every referenced filename includes `tts`.",
            self,
        )
        self.overwrite_tts_note.setWordWrap(True)

        self.reference_label = WrappingPathLabel()
        self.reference_label.set_path_text(
            self._display_asset_path(self.config.reference_audio_path)
        )
        self.transcript_label = WrappingPathLabel()
        self.transcript_label.set_path_text(
            self._display_asset_path(self.config.transcript_path)
        )

        self.mapping_table = self._build_mapping_table()
        self.header_table = self._build_header_table()
        self._refresh_mapping_table()
        self._refresh_header_table()

        content = QWidget(self)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self._build_endpoint_group())
        content_layout.addWidget(self._build_assets_group())
        content_layout.addWidget(self._build_options_group())
        content_layout.addWidget(self._build_mappings_group())
        content_layout.addWidget(self._build_headers_group())
        content_layout.addStretch(1)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)

        root = QVBoxLayout(self)
        root.addWidget(scroll)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        qconnect(buttons.accepted, self.accept)
        qconnect(buttons.rejected, self.reject)
        root.addWidget(buttons)

        self._apply_initial_size(parent)

    def _apply_initial_size(self, parent: QWidget) -> None:
        parent_size = parent.size() if parent else mw.size()
        width = min(max(760, int(parent_size.width() * 0.68)), int(parent_size.width() * 0.9))
        height = max(560, int(parent_size.height() * 0.82))
        self.resize(width, height)
        self.setMinimumWidth(720)
        self.setMaximumWidth(max(760, int(parent_size.width() * 0.92)))
        self.setMinimumHeight(520)

    def _build_endpoint_group(self) -> QGroupBox:
        group = QGroupBox("Endpoint")
        form = QFormLayout(group)
        form.addRow("Host", self.host_edit)
        form.addRow("Port", self.port_spin)
        form.addRow("Path", self.path_edit)
        form.addRow("Timeout (seconds)", self.timeout_spin)
        form.addRow("Text form field", self.text_field_edit)
        form.addRow("Reference audio form field", self.reference_audio_field_edit)
        form.addRow("Transcript text form field", self.transcript_field_edit)
        return group

    def _build_assets_group(self) -> QGroupBox:
        group = QGroupBox("Global Reference Assets")
        layout = QGridLayout(group)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)

        reference_button = QPushButton("Import reference audio...", self)
        clear_reference_button = QPushButton("Clear", self)
        transcript_button = QPushButton("Import transcript...", self)
        clear_transcript_button = QPushButton("Clear", self)
        open_folder_button = QPushButton("Show user_files folder", self)
        for button in (
            reference_button,
            clear_reference_button,
            transcript_button,
            clear_transcript_button,
            open_folder_button,
        ):
            button.setSizePolicy(
                QSizePolicy.Policy.Fixed,
                QSizePolicy.Policy.Fixed,
            )

        qconnect(reference_button.clicked, self._pick_reference_audio)
        qconnect(clear_reference_button.clicked, self._clear_reference_audio)
        qconnect(transcript_button.clicked, self._pick_transcript)
        qconnect(clear_transcript_button.clicked, self._clear_transcript)
        qconnect(open_folder_button.clicked, self._show_user_files_hint)

        layout.addWidget(QLabel("Reference audio"), 0, 0)
        layout.addWidget(self.reference_label, 0, 1)
        layout.addWidget(reference_button, 0, 2)
        layout.addWidget(clear_reference_button, 0, 3)
        layout.addWidget(QLabel("Transcript"), 1, 0)
        layout.addWidget(self.transcript_label, 1, 1)
        layout.addWidget(transcript_button, 1, 2)
        layout.addWidget(clear_transcript_button, 1, 3)
        layout.addWidget(open_folder_button, 2, 2, 1, 2)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 0)
        layout.setColumnStretch(3, 0)
        return group

    def _build_options_group(self) -> QGroupBox:
        group = QGroupBox("Generation Options")
        layout = QVBoxLayout(group)
        layout.addWidget(self.overwrite_tts_checkbox)
        layout.addWidget(self.overwrite_tts_note)
        return group

    def _build_mappings_group(self) -> QGroupBox:
        group = QGroupBox("Deck and Note Type Mappings")
        layout = QVBoxLayout(group)
        layout.addWidget(self.mapping_table)

        buttons = QHBoxLayout()
        add_button = QPushButton("Add mapping", self)
        edit_button = QPushButton("Edit mapping", self)
        remove_button = QPushButton("Remove mapping", self)
        qconnect(add_button.clicked, self._add_mapping)
        qconnect(edit_button.clicked, self._edit_mapping)
        qconnect(remove_button.clicked, self._remove_mapping)
        buttons.addWidget(add_button)
        buttons.addWidget(edit_button)
        buttons.addWidget(remove_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        return group

    def _build_headers_group(self) -> QGroupBox:
        group = QGroupBox("Custom Headers")
        layout = QVBoxLayout(group)
        layout.addWidget(self.header_table)

        buttons = QHBoxLayout()
        add_button = QPushButton("Add header", self)
        edit_button = QPushButton("Edit header", self)
        remove_button = QPushButton("Remove header", self)
        qconnect(add_button.clicked, self._add_header)
        qconnect(edit_button.clicked, self._edit_header)
        qconnect(remove_button.clicked, self._remove_header)
        buttons.addWidget(add_button)
        buttons.addWidget(edit_button)
        buttons.addWidget(remove_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        return group

    def _build_mapping_table(self) -> QTableWidget:
        table = QTableWidget(self)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(
            ["Deck", "Note Type", "Source Field", "Target Field"]
        )
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return table

    def _build_header_table(self) -> QTableWidget:
        table = QTableWidget(self)
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Header", "Value"])
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return table

    def _refresh_mapping_table(self) -> None:
        self.mapping_table.setRowCount(len(self.mappings))
        for row, mapping in enumerate(self.mappings):
            self.mapping_table.setItem(row, 0, QTableWidgetItem(mapping.deck_name))
            self.mapping_table.setItem(row, 1, QTableWidgetItem(mapping.note_type_name))
            self.mapping_table.setItem(row, 2, QTableWidgetItem(mapping.source_field))
            self.mapping_table.setItem(row, 3, QTableWidgetItem(mapping.target_field))

    def _refresh_header_table(self) -> None:
        self.header_table.setRowCount(len(self.headers))
        for row, header in enumerate(self.headers):
            self.header_table.setItem(row, 0, QTableWidgetItem(header.name))
            self.header_table.setItem(row, 1, QTableWidgetItem(header.value))

    def _selected_row(self, table: QTableWidget) -> int | None:
        indexes = table.selectionModel().selectedRows()
        if not indexes:
            return None
        return indexes[0].row()

    def _add_mapping(self) -> None:
        dialog = MappingEditorDialog(self)
        if dialog.exec():
            self.mappings.append(dialog.mapping())
            self._refresh_mapping_table()

    def _edit_mapping(self) -> None:
        row = self._selected_row(self.mapping_table)
        if row is None:
            showInfo("Select a mapping to edit.")
            return
        dialog = MappingEditorDialog(self, self.mappings[row])
        if dialog.exec():
            self.mappings[row] = dialog.mapping()
            self._refresh_mapping_table()

    def _remove_mapping(self) -> None:
        row = self._selected_row(self.mapping_table)
        if row is None:
            showInfo("Select a mapping to remove.")
            return
        del self.mappings[row]
        self._refresh_mapping_table()

    def _add_header(self) -> None:
        dialog = HeaderEditorDialog(self)
        if dialog.exec():
            self.headers.append(dialog.header())
            self._refresh_header_table()

    def _edit_header(self) -> None:
        row = self._selected_row(self.header_table)
        if row is None:
            showInfo("Select a header to edit.")
            return
        dialog = HeaderEditorDialog(self, self.headers[row])
        if dialog.exec():
            self.headers[row] = dialog.header()
            self._refresh_header_table()

    def _remove_header(self) -> None:
        row = self._selected_row(self.header_table)
        if row is None:
            showInfo("Select a header to remove.")
            return
        del self.headers[row]
        self._refresh_header_table()

    def _pick_reference_audio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select reference audio",
            "",
            "Audio files (*.wav *.mp3 *.flac *.m4a *.ogg *.opus);;All files (*)",
        )
        if path:
            self.reference_source_path = path
            self.reference_label.set_path_text(path)

    def _pick_transcript(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select transcript text file",
            "",
            "Text files (*.txt);;All files (*)",
        )
        if path:
            self.transcript_source_path = path
            self.transcript_label.set_path_text(path)

    def _clear_reference_audio(self) -> None:
        self.reference_source_path = ""
        self.config.reference_audio_path = ""
        self.reference_label.set_path_text(self._display_asset_path(""))

    def _clear_transcript(self) -> None:
        self.transcript_source_path = ""
        self.config.transcript_path = ""
        self.transcript_label.set_path_text(self._display_asset_path(""))

    def _show_user_files_hint(self) -> None:
        showInfo(f"user_files folder:\n{USER_FILES_DIR}")

    def _display_asset_path(self, relative_path: str) -> str:
        if not relative_path:
            return "Not configured"
        return str((USER_FILES_DIR / relative_path).resolve())

    def _validate(self) -> str | None:
        if not self.host_edit.text().strip():
            return "Host cannot be empty."
        if not self.path_edit.text().strip():
            return "Path cannot be empty."
        if not self.text_field_edit.text().strip():
            return "The text form field name cannot be empty."
        if not self.reference_audio_field_edit.text().strip():
            return "The reference audio form field name cannot be empty."
        seen: set[tuple[str, str]] = set()
        for mapping in self.mappings:
            key = (mapping.deck_name, mapping.note_type_name)
            if key in seen:
                return (
                    "Each deck and note type combination can only appear once in the mapping table."
                )
            seen.add(key)
        return None

    def accept(self) -> None:
        error = self._validate()
        if error:
            QMessageBox.warning(self, "Invalid settings", error)
            return

        reference_audio_path = self.config.reference_audio_path
        transcript_path = self.config.transcript_path
        try:
            if self.reference_source_path:
                reference_audio_path = import_asset(
                    self.reference_source_path, "reference_audio"
                )
            if self.transcript_source_path:
                transcript_path = import_asset(
                    self.transcript_source_path, "transcript"
                )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Asset import failed",
                f"Could not copy the selected file into user_files:\n{exc}",
            )
            return

        config = AddonConfig(
            endpoint=EndpointConfig(
                host=self.host_edit.text().strip(),
                port=self.port_spin.value(),
                path=self.path_edit.text().strip(),
                timeout_seconds=self.timeout_spin.value(),
                text_field_name=self.text_field_edit.text().strip(),
                reference_audio_field_name=self.reference_audio_field_edit.text().strip(),
                transcript_text_field_name=self.transcript_field_edit.text().strip(),
            ),
            headers=[replace(header) for header in self.headers if header.name],
            reference_audio_path=reference_audio_path,
            transcript_path=transcript_path,
            overwrite_existing_tts_audio=self.overwrite_tts_checkbox.isChecked(),
            mappings=[replace(mapping) for mapping in self.mappings],
        )
        save_config(config)
        super().accept()


def show_config_dialog() -> None:
    dialog = ConfigDialog(mw)
    dialog.exec()
