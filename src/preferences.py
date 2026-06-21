from gi.repository import Adw, Gio, GLib, Gtk


@Gtk.Template(resource_path="/io/github/eucaue/flexa/preferences-dialog.ui")
class FlexaPreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = "FlexaPreferencesDialog"

    output_dir_row: Adw.EntryRow = Gtk.Template.Child()
    btn_browse_output: Gtk.Button = Gtk.Template.Child()

    output_dir_windows_row: Adw.EntryRow = Gtk.Template.Child()
    btn_browse_output_windows: Gtk.Button = Gtk.Template.Child()

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

    def __init__(self, settings, **kwargs):
        super().__init__(**kwargs)
        self.settings = settings
        self.settings.bind(
            "output-dir", self.output_dir_row, "text", Gio.SettingsBindFlags.DEFAULT
        )
        if self.settings.get_string("output-dir") == "":
            self.output_dir_row.set_text("~/.local/share/icons")

        self.settings.bind(
            "output-dir-windows", self.output_dir_windows_row, "text", Gio.SettingsBindFlags.DEFAULT
        )
        if self.settings.get_string("output-dir-windows") == "":
            self.output_dir_windows_row.set_text("~/Cursors")

        self.btn_browse_output.connect("clicked", self._on_select_folders)
        self.btn_browse_output_windows.connect("clicked", self._on_select_folders_windows)
