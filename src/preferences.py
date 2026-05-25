from gi.repository import Adw, Gio, Gtk


@Gtk.Template(resource_path="/io/github/eucaue/flexa/preferences-dialog.ui")
class FlexaPreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = "FlexaPreferencesDialog"

    output_dir_row: Adw.EntryRow = Gtk.Template.Child()

    def __init__(self, settings, **kwargs):
        super().__init__(**kwargs)
        self.settings = settings
        self.settings.bind(
            "output-dir", self.output_dir_row, "text", Gio.SettingsBindFlags.DEFAULT
        )
