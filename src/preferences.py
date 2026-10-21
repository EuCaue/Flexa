# preferences.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import platform
import threading
from gettext import gettext as _
from pathlib import Path
from typing import Callable, cast

from gi.repository import Adw, Gio, GLib, GObject, Gtk, Pango

from .cursor_converter import BaseCursorConverter, host_path, short_home, stored_path
from .debug import debug


@Gtk.Template(resource_path="/io/github/eucaue/flexa/preferences-dialog.ui")
class FlexaPreferencesDialog(Adw.PreferencesDialog):
    """Preferences dialog for Flexa configuration."""

    __gtype_name__ = "FlexaPreferencesDialog"

    output_dir_row: Adw.EntryRow = Gtk.Template.Child()
    btn_browse_output: Gtk.Button = Gtk.Template.Child()

    output_dir_windows_row: Adw.EntryRow = Gtk.Template.Child()
    btn_browse_output_windows: Gtk.Button = Gtk.Template.Child()
    fallback_linux_row: Adw.ComboRow = Gtk.Template.Child()
    fallback_windows_row: Adw.ComboRow = Gtk.Template.Child()
    btn_browse_fallback_linux: Gtk.Button = Gtk.Template.Child()
    btn_browse_fallback_windows: Gtk.Button = Gtk.Template.Child()

    def _select_output_folder(self, target_row: Adw.EntryRow) -> None:
        dialog = Gtk.FileDialog()
        parent = cast(Gtk.Window | None, self.get_root())

        def _on_finish(dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
            try:
                folder = dialog.select_folder_finish(result)
                if folder:
                    path = folder.get_path()
                    if path:
                        parsed_path = self._parse_home_folder(path)
                        target_row.set_text(parsed_path)
            except GLib.GError as err:
                debug(f"Folder selection error: {err}")

        dialog.select_folder(parent=parent, callback=_on_finish)

    def _parse_home_folder(self, path: str) -> str:
        return short_home(stored_path(path))

    @staticmethod
    def _has_linux_cursors(path: Path) -> bool:
        try:
            return path.is_dir() and any(
                item.is_file() and not item.suffix for item in path.iterdir()
            )
        except OSError as err:
            debug(f"Error checking Linux cursors in {path}: {err}")
            return False

    @staticmethod
    def _has_windows_cursors(path: Path) -> bool:
        try:
            return path.is_dir() and any(
                item.is_file() and item.suffix.lower() in {".cur", ".ani"}
                for item in path.iterdir()
            )
        except OSError as err:
            debug(f"Error checking Windows cursors in {path}: {err}")
            return False

    @staticmethod
    def _display_path(path: Path) -> str:
        expanded = path.expanduser()
        return stored_path(str(expanded if expanded.is_absolute() else expanded.absolute()))

    @classmethod
    def find_linux_fallback_paths(cls, settings: Gio.Settings) -> list[str]:
        # Inside Flatpak, XDG_DATA_HOME points to the app's private data dir,
        # whose themes the rest of the desktop cannot use.
        if "FLATPAK_ID" in os.environ:
            data_home = Path("~/.local/share").expanduser()
        else:
            data_home = Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser()
        data_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
        roots = [Path("~/.icons").expanduser(), data_home / "icons"]
        roots.extend(Path(data_dir) / "icons" for data_dir in data_dirs if data_dir)
        custom = settings.get_string("fallback-root-linux")
        if custom:
            roots.append(Path(custom))
        return cls._find_cursor_paths(roots, "cursors", cls._has_linux_cursors)

    @classmethod
    def find_windows_fallback_paths(cls, settings: Gio.Settings) -> list[str]:
        roots = [
            Path(os.environ["WINDIR"]) / "Cursors" if os.environ.get("WINDIR") else None,
            Path(os.environ["LOCALAPPDATA"]) / "Microsoft/Windows/Cursors"
            if os.environ.get("LOCALAPPDATA")
            else None,
            Path(os.environ["APPDATA"]) / "Microsoft/Windows/Cursors"
            if os.environ.get("APPDATA")
            else None,
            Path("~/Documents/Windows Cursors").expanduser(),
        ]
        custom = settings.get_string("fallback-root-windows")
        if custom:
            roots.append(Path(custom))
        return cls._find_cursor_paths(
            [root for root in roots if root], None, cls._has_windows_cursors
        )

    @staticmethod
    def _find_cursor_paths(
        roots: list[Path],
        subdirectory: str | None,
        is_cursor_directory: Callable[[Path], bool],
        max_depth: int = 2,
    ) -> list[str]:
        found: set[str] = set()

        def scan(directory: Path, depth: int) -> None:
            if not directory.is_dir():
                return
            candidate = directory / subdirectory if subdirectory else directory
            if is_cursor_directory(candidate):
                found.add(FlexaPreferencesDialog._display_path(directory))
                return  # Found a cursor theme, stop recursing into its subdirectories!

            if depth >= max_depth:
                return
            try:
                children = list(directory.iterdir())
            except OSError as err:
                debug(f"Error scanning directory {directory}: {err}")
                return
            for child in children:
                if child.is_dir() and not child.name.startswith("."):
                    scan(child, depth + 1)

        for root in roots:
            scan(root, 0)
        return sorted(found)

    def _setup_fallback_row(self, row: Adw.ComboRow, key: str, paths: list[str]) -> None:
        raw_saved_path = self.settings.get_string(key)
        saved_path = self._display_path(Path(raw_saved_path)) if raw_saved_path else ""
        if saved_path != raw_saved_path:
            self.settings.set_string(key, saved_path)
        values: list[str | None] = [None, *paths]
        labels = [_("None"), *(Path(p).name for p in paths)]

        if saved_path and saved_path not in paths:
            values.append(saved_path)
            name = Path(saved_path).name
            if BaseCursorConverter.resolve_fallback_path(Path(saved_path)).exists():
                labels.append(name)
            else:
                labels.append(_("Unavailable: {path}").format(path=name))

        selected_index = values.index(saved_path) if saved_path in values else 0

        handler_id = getattr(row, "_fallback_handler_id", None)
        if handler_id is not None and GObject.signal_handler_is_connected(row, handler_id):
            row.disconnect(handler_id)

        setattr(row, "_fallback_values", values)
        row.set_model(Gtk.StringList.new(labels))
        row.set_selected(selected_index)
        row.set_tooltip_text(self._fallback_location(values[selected_index]))

        new_handler_id = row.connect(
            "notify::selected", self._on_fallback_selected, key, values
        )
        setattr(row, "_fallback_handler_id", new_handler_id)

    @staticmethod
    def _fallback_location(value: str | None) -> str | None:
        return short_home(host_path(value)) if value else None

    def _setup_fallback_list_factory(self, row: Adw.ComboRow) -> None:
        """Show each theme's location under its name in the dropdown."""
        factory = Gtk.SignalListItemFactory()

        def _setup(_factory, item: Gtk.ListItem) -> None:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            title = Gtk.Label(xalign=0)
            subtitle = Gtk.Label(
                xalign=0,
                ellipsize=Pango.EllipsizeMode.MIDDLE,
                max_width_chars=40,
                css_classes=["dim-label", "caption"],
            )
            box.append(title)
            box.append(subtitle)
            item.set_child(box)

        def _bind(_factory, item: Gtk.ListItem) -> None:
            box = cast(Gtk.Box, item.get_child())
            title = cast(Gtk.Label, box.get_first_child())
            subtitle = cast(Gtk.Label, title.get_next_sibling())
            string = cast(Gtk.StringObject, item.get_item())
            title.set_label(string.get_string())
            values: list[str | None] = getattr(row, "_fallback_values", [])
            position = item.get_position()
            location = self._fallback_location(values[position]) if position < len(values) else None
            subtitle.set_label(location or "")
            subtitle.set_visible(location is not None)

        factory.connect("setup", _setup)
        factory.connect("bind", _bind)
        row.set_list_factory(factory)
        row.set_expression(Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"))
        row.set_enable_search(True)
        if hasattr(row, "set_search_match_mode"):
            row.set_search_match_mode(Gtk.StringFilterMatchMode.SUBSTRING)

    def _on_fallback_selected(
        self, row: Adw.ComboRow, _pspec, key: str, values: list[str | None]
    ) -> None:
        selected = row.get_selected()
        if 0 <= selected < len(values):
            val = values[selected]
            row.set_tooltip_text(self._fallback_location(val))
            self.settings.set_string(key, val or "")

    def _select_fallback_root(self, mode: str) -> None:
        dialog = Gtk.FileDialog()
        parent = cast(Gtk.Window | None, self.get_root())

        def _on_finish(dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
            try:
                folder = dialog.select_folder_finish(result)
                if folder:
                    path = folder.get_path()
                    if path:
                        self._apply_fallback_root(path, mode)
            except GLib.GError as err:
                debug(f"Fallback folder selection error: {err}")

        dialog.select_folder(parent=parent, callback=_on_finish)

    def _apply_fallback_root(self, path: str, mode: str) -> None:
        if mode == "linux":
            subdir, checker = "cursors", self._has_linux_cursors
            root_key, row, key, finder = (
                "fallback-root-linux",
                self.fallback_linux_row,
                "fallback-theme-path-linux",
                self.find_linux_fallback_paths,
            )
        else:
            subdir, checker = None, self._has_windows_cursors
            root_key, row, key, finder = (
                "fallback-root-windows",
                self.fallback_windows_row,
                "fallback-theme-path-windows",
                self.find_windows_fallback_paths,
            )

        if not self._find_cursor_paths([Path(path)], subdir, checker):
            self._show_invalid_fallback_root_dialog()
            return
        self.settings.set_string(root_key, self._display_path(Path(path)))
        paths = finder(self.settings)
        FallbackScan.update(mode, paths)
        self._setup_fallback_row(row, key, paths)

    def _show_invalid_fallback_root_dialog(self) -> None:
        dialog = Adw.AlertDialog(
            heading=_("No cursor themes found"),
            body=_("The selected folder does not contain cursor themes."),
        )
        dialog.add_response("ok", _("OK"))
        dialog.set_default_response("ok")
        dialog.present(cast(Gtk.Widget, self.get_root()))

    def _set_fallback_loading(self, loading: bool) -> None:
        for row, spinner in (
            (self.fallback_linux_row, self._linux_spinner),
            (self.fallback_windows_row, self._windows_spinner),
        ):
            row.set_sensitive(not loading)
            spinner.set_visible(loading)
            spinner.set_spinning(loading)

    def _on_fallback_paths_loaded(self, linux_paths: list[str], windows_paths: list[str]) -> None:
        self._set_fallback_loading(False)
        self._setup_fallback_row(
            self.fallback_linux_row,
            "fallback-theme-path-linux",
            linux_paths,
        )
        self._setup_fallback_row(
            self.fallback_windows_row,
            "fallback-theme-path-windows",
            windows_paths,
        )

    def __init__(self, settings: Gio.Settings, **kwargs) -> None:
        super().__init__(**kwargs)
        self.settings = settings
        self.settings.bind(
            "output-dir", self.output_dir_row, "text", Gio.SettingsBindFlags.DEFAULT
        )
        if self.settings.get_string("output-dir") == "":
            if os.name == "nt":
                self.output_dir_row.set_text("~\\Documents\\Linux Cursors")
            else:
                self.output_dir_row.set_text("~/.local/share/icons")

        self.settings.bind(
            "output-dir-windows",
            self.output_dir_windows_row,
            "text",
            Gio.SettingsBindFlags.DEFAULT,
        )
        if self.settings.get_string("output-dir-windows") == "":
            if os.name == "nt":
                self.output_dir_windows_row.set_text("~\\Documents\\Windows Cursors")
            else:
                self.output_dir_windows_row.set_text("~/Documents/Windows Cursors")

        self.btn_browse_output.connect(
            "clicked", lambda _: self._select_output_folder(self.output_dir_row)
        )
        self.btn_browse_output_windows.connect(
            "clicked", lambda _: self._select_output_folder(self.output_dir_windows_row)
        )
        self.btn_browse_fallback_linux.connect(
            "clicked", lambda _: self._select_fallback_root("linux")
        )
        self.btn_browse_fallback_windows.connect(
            "clicked", lambda _: self._select_fallback_root("windows")
        )
        system = platform.system()
        self.btn_browse_fallback_linux.set_visible(system != "Linux")
        self.btn_browse_fallback_windows.set_visible(system != "Windows")

        self._setup_fallback_list_factory(self.fallback_linux_row)
        self._setup_fallback_list_factory(self.fallback_windows_row)

        for row in (self.fallback_linux_row, self.fallback_windows_row):
            row.set_model(Gtk.StringList.new([_("Loading…")]))

        self._linux_spinner = Gtk.Spinner(valign=Gtk.Align.CENTER)
        self._windows_spinner = Gtk.Spinner(valign=Gtk.Align.CENTER)
        self.fallback_linux_row.add_suffix(self._linux_spinner)
        self.fallback_windows_row.add_suffix(self._windows_spinner)
        self._set_fallback_loading(True)

        FallbackScan.request(self.settings, self._on_fallback_paths_loaded)


class FallbackScan:
    """Scans fallback cursor themes once per run and shares the result.

    Hosts can have thousands of cursor themes, so the scan starts when the
    app starts and the preferences dialog reuses its result.
    """

    _lock = threading.Lock()
    _result: tuple[list[str], list[str]] | None = None
    _running = False
    _callbacks: list[Callable[[list[str], list[str]], None]] = []

    @classmethod
    def start(cls, settings: Gio.Settings) -> None:
        with cls._lock:
            if cls._result is not None or cls._running:
                return
            cls._running = True
        threading.Thread(target=cls._scan, args=(settings,), daemon=True).start()

    @classmethod
    def request(
        cls, settings: Gio.Settings, callback: Callable[[list[str], list[str]], None]
    ) -> None:
        """Call callback on the main loop with (linux_paths, windows_paths)."""
        with cls._lock:
            result = cls._result
            if result is None:
                cls._callbacks.append(callback)
        if result is not None:
            callback(*result)
        else:
            cls.start(settings)

    @classmethod
    def update(cls, mode: str, paths: list[str]) -> None:
        with cls._lock:
            if cls._result is not None:
                linux, windows = cls._result
                cls._result = (paths, windows) if mode == "linux" else (linux, paths)

    @classmethod
    def _scan(cls, settings: Gio.Settings) -> None:
        result = (
            FlexaPreferencesDialog.find_linux_fallback_paths(settings),
            FlexaPreferencesDialog.find_windows_fallback_paths(settings),
        )
        GLib.idle_add(cls._finish, result)

    @classmethod
    def _finish(cls, result: tuple[list[str], list[str]]) -> bool:
        with cls._lock:
            cls._result = result
            cls._running = False
            callbacks, cls._callbacks = cls._callbacks, []
        for callback in callbacks:
            callback(*result)
        return False
