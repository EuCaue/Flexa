import os
import platform
from gettext import gettext as _
from pathlib import Path
from typing import cast

from gi.repository import Adw, Gio, GLib, Gtk


@Gtk.Template(resource_path="/io/github/eucaue/flexa/preferences-dialog.ui")
class FlexaPreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = "FlexaPreferencesDialog"

    output_dir_row: Adw.EntryRow = Gtk.Template.Child()
    btn_browse_output: Gtk.Button = Gtk.Template.Child()

    output_dir_windows_row: Adw.EntryRow = Gtk.Template.Child()
    btn_browse_output_windows: Gtk.Button = Gtk.Template.Child()
    fallback_linux_row: Adw.ComboRow = Gtk.Template.Child()
    fallback_windows_row: Adw.ComboRow = Gtk.Template.Child()
    btn_browse_fallback_linux: Gtk.Button = Gtk.Template.Child()
    btn_browse_fallback_windows: Gtk.Button = Gtk.Template.Child()

    def _on_select_folders(self, widget):
        dialog = Gtk.FileDialog()
        dialog.select_folder(parent=self.get_root(), callback=self._on_folder_selected)

    def _on_select_folders_windows(self, widget):
        dialog = Gtk.FileDialog()
        dialog.select_folder(parent=self.get_root(), callback=self._on_folder_selected_windows)

    def _on_folder_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            path = folder.get_path()
            parsed_path = self._parse_home_folder(path)
            self.output_dir_row.set_text(parsed_path)
        except GLib.GError:
            pass

    def _on_folder_selected_windows(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            path = folder.get_path()
            parsed_path = self._parse_home_folder(path)
            self.output_dir_windows_row.set_text(parsed_path)
        except GLib.GError:
            pass

    def _parse_home_folder(self, path) -> str:
        return path.replace(GLib.get_home_dir(), "~", 1)

    def _handle_default(self):
        self.output_dir_row.set_text("~/.local/share/icons")

    @staticmethod
    def _has_linux_cursors(path: Path) -> bool:
        try:
            return path.is_dir() and any(
                item.is_file() and not item.suffix for item in path.iterdir()
            )
        except OSError:
            return False

    @staticmethod
    def _has_windows_cursors(path: Path) -> bool:
        try:
            return path.is_dir() and any(
                item.is_file() and item.suffix.lower() in {".cur", ".ani"}
                for item in path.iterdir()
            )
        except OSError:
            return False

    @staticmethod
    def _display_path(path: Path) -> str:
        expanded = path.expanduser()
        value = str(expanded if expanded.is_absolute() else expanded.absolute())
        replacements = (
            ("/run/host/share/icons", "/usr/share/icons"),
            ("/run/host/usr/share/icons", "/usr/share/icons"),
            ("/run/host/usr/local/share/icons", "/usr/local/share/icons"),
        )
        for sandbox_path, system_path in replacements:
            if value == sandbox_path or value.startswith(sandbox_path + os.sep):
                return system_path + value[len(sandbox_path) :]
        return value

    def _find_linux_fallback_paths(self) -> list[str]:
        data_home = Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser()
        data_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
        roots = [Path("~/.icons").expanduser(), data_home / "icons"]
        roots.extend(Path(data_dir) / "icons" for data_dir in data_dirs if data_dir)
        custom = self.settings.get_string("fallback-root-linux")
        if custom:
            roots.append(Path(custom))
        return self._find_cursor_paths(roots, "cursors", self._has_linux_cursors)

    def _find_windows_fallback_paths(self) -> list[str]:
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
        custom = self.settings.get_string("fallback-root-windows")
        if custom:
            roots.append(Path(custom))
        return self._find_cursor_paths(
            [root for root in roots if root], None, self._has_windows_cursors
        )

    @staticmethod
    def _find_cursor_paths(
        roots: list[Path], subdirectory: str | None, is_cursor_directory, max_depth: int = 3
    ) -> list[str]:
        found: set[str] = set()

        def scan(directory: Path, depth: int) -> None:
            candidate = directory / subdirectory if subdirectory else directory
            if is_cursor_directory(candidate):
                found.add(FlexaPreferencesDialog._display_path(directory))
            if depth >= max_depth or not directory.is_dir():
                return
            try:
                children = list(directory.iterdir())
            except OSError:
                return
            for child in children:
                if child.is_dir():
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
        labels = [_("None"), *(p.replace(GLib.get_home_dir(), "~", 1) for p in paths)]

        if saved_path and saved_path not in paths:
            values.append(saved_path)
            if Path(saved_path).exists():
                labels.append(saved_path.replace(GLib.get_home_dir(), "~", 1))
            else:
                labels.append(
                    _("Unavailable: {path}").format(
                        path=saved_path.replace(GLib.get_home_dir(), "~", 1)
                    )
                )
        row.set_model(Gtk.StringList.new(labels))
        row.set_selected(values.index(saved_path) if saved_path in values else 0)
        row.set_tooltip_text(values[row.get_selected()] or None)
        row.connect("notify::selected", self._on_fallback_selected, key, values)

    def _on_fallback_selected(self, row: Adw.ComboRow, _pspec, key: str, values: list[str | None]):
        row.set_tooltip_text(values[row.get_selected()] or None)
        self.settings.set_string(key, values[row.get_selected()] or "")

    def _on_select_fallback_folders(self, widget):
        dialog = Gtk.FileDialog()
        parent = cast(Gtk.Window, self.get_root())
        dialog.select_folder(parent=parent, callback=self._on_fallback_root_selected)

    def _on_select_fallback_folders_windows(self, widget):
        dialog = Gtk.FileDialog()
        parent = cast(Gtk.Window, self.get_root())
        dialog.select_folder(parent=parent, callback=self._on_fallback_root_selected_windows)

    def _on_fallback_root_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.GError:
            return
        self._apply_fallback_root(folder.get_path(), "linux")

    def _on_fallback_root_selected_windows(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.GError:
            return
        self._apply_fallback_root(folder.get_path(), "windows")

    def _apply_fallback_root(self, path: str, mode: str) -> None:
        if mode == "linux":
            subdir, checker = "cursors", self._has_linux_cursors
            root_key, row, key, finder = (
                "fallback-root-linux",
                self.fallback_linux_row,
                "fallback-theme-path-linux",
                self._find_linux_fallback_paths,
            )
        else:
            subdir, checker = None, self._has_windows_cursors
            root_key, row, key, finder = (
                "fallback-root-windows",
                self.fallback_windows_row,
                "fallback-theme-path-windows",
                self._find_windows_fallback_paths,
            )

        if not self._find_cursor_paths([Path(path)], subdir, checker):
            self._show_invalid_fallback_root_dialog()
            return
        self.settings.set_string(root_key, self._display_path(Path(path)))
        self._setup_fallback_row(row, key, finder())

    def _show_invalid_fallback_root_dialog(self):
        dialog = Adw.AlertDialog(
            heading=_("No cursor themes found"),
            body=_("The selected folder does not contain cursor themes."),
        )
        dialog.add_response("ok", _("OK"))
        dialog.set_default_response("ok")
        dialog.present(cast(Gtk.Widget, self.get_root()))

    def __init__(self, settings, **kwargs):
        super().__init__(**kwargs)
        self.settings = settings
        self.settings.bind("output-dir", self.output_dir_row, "text", Gio.SettingsBindFlags.DEFAULT)
        if self.settings.get_string("output-dir") == "":
            if os.name == "nt":
                self.output_dir_row.set_text("~\\Documents\\Linux Cursors")
            else:
                self.output_dir_row.set_text("~/.local/share/icons")

        self.settings.bind(
            "output-dir-windows", self.output_dir_windows_row, "text", Gio.SettingsBindFlags.DEFAULT
        )
        if self.settings.get_string("output-dir-windows") == "":
            if os.name == "nt":
                self.output_dir_windows_row.set_text("~\\Documents\\Windows Cursors")
            else:
                self.output_dir_windows_row.set_text("~/Documents/Windows Cursors")

        self.btn_browse_output.connect("clicked", self._on_select_folders)
        self.btn_browse_output_windows.connect("clicked", self._on_select_folders_windows)
        self.btn_browse_fallback_linux.connect("clicked", self._on_select_fallback_folders)
        self.btn_browse_fallback_windows.connect(
            "clicked", self._on_select_fallback_folders_windows
        )
        system = platform.system()
        self.btn_browse_fallback_linux.set_visible(system != "Linux")
        self.btn_browse_fallback_windows.set_visible(system != "Windows")
        self._setup_fallback_row(
            self.fallback_linux_row,
            "fallback-theme-path-linux",
            self._find_linux_fallback_paths(),
        )
        self._setup_fallback_row(
            self.fallback_windows_row,
            "fallback-theme-path-windows",
            self._find_windows_fallback_paths(),
        )
