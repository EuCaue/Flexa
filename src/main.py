# main.py
#
# Copyright 2026 caue
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
from gettext import gettext as _

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from dataclasses import dataclass
from pathlib import Path

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from .cursor_converter import ConversionResult, ConversionStatus, CursorConverter
from .preferences import FlexaPreferencesDialog
from .window import FlexaWindow


@dataclass
class RowData:
    row_name: str
    folder_path: str
    stack: Gtk.Stack
    spinner: Gtk.Spinner


class FlexaApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id="io.github.eucaue.flexa",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            resource_base_path="/io/github/eucaue/flexa",
        )
        self._create_action("quit", lambda *_: self.quit(), ["<control>q"])
        self._create_action("about", self.on_about_action)
        self._create_action("preferences", self.on_preferences_action)
        self._create_action("shortcuts", self.on_shortcuts_action, ["<control>comma"])
        self.folder_rows: list[RowData] = []
        self.folder_dialog: Gtk.FileDialog = Gtk.FileDialog()
        self.empty_status_page: Adw.StatusPage = Adw.StatusPage(
            title=_("No Folders Added"),
            description=_("Drag folders here or click the button below"),
            icon_name="folder-symbolic",
        )
        self.window = None
        self.settings = Gio.Settings(schema_id="io.github.eucaue.flexa")
        self.converter: CursorConverter | None = None

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = FlexaWindow(application=self)
        self.window = win
        win.present()
        self.connect_signals()

    def connect_signals(self):
        self.window.btn_add.connect("clicked", self.on_add_folders)
        self.window.btn_convert.connect("clicked", self.on_convert_files)
        self.setup_drop_target()
        self.setup_empty_state()

    def _create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name="Flexa",
            application_icon="io.github.eucaue.flexa",
            developer_name="EuCaue",
            version="1.0.0",
            comments=_("A simple GNOME app to convert Windows cursor themes to Linux format."),
            # TODO:
            website="https://github.com/eucaue/",
            issue_url="https://github.com/eucaue/flexa/issues",
            translator_credits=_("EuCaue"),
            developers=["EuCaue"],
            copyright="© 2026 EuCaue",
        )
        about.add_link(_("Donate"), "https://github.com/sponsors/eucaue")
        about.add_link(_("Quick Lofi"), "https://github.com/eucaue/quick-lofi")
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        preferences = FlexaPreferencesDialog(settings=self.settings)
        preferences.present(self.props.active_window)
        print("app.preferences action activated")

    def on_shortcuts_action(self, widget, _):
        print("app shortcuts called...")
        builder = Gtk.Builder.new_from_resource("/io/github/eucaue/flexa/shortcuts-dialog.ui")
        dialog = builder.get_object("shortcuts_dialog")
        dialog.present(self.props.active_window)

    def on_add_folders(self, widget):
        """Callback for the app.add_files action."""
        print("Opened dialog")
        self.folder_dialog.set_title(_("Select cursor folders"))
        self.folder_dialog.select_multiple_folders(self.window, None, self.on_select_folders, None)

    def on_select_folders(self, dialog, result, _):
        try:
            folders_model = dialog.select_multiple_folders_finish(result)
        except GLib.GError:
            return

        if folders_model is None:
            return

        folders = [
            (f.get_path(), f.get_basename())
            for i in range(folders_model.get_n_items())
            if (f := folders_model.get_item(i))
        ]

        self._add_folders(folders)

    def _add_folders(self, folders: list[tuple[str, str]]) -> int:
        """
        Receives list of (path, name), validates and adds the rows.
        Returns the number of folders added.
        """
        added = 0
        rejected = []

        for folder_path, folder_name in folders:
            if not folder_path:
                continue
            if self._folder_already_added(folder_path):
                continue
            if not self._has_cursor_files(folder_path):
                rejected.append(folder_name)
                continue

            row = self.on_create_folder_row(folder_name, folder_path)
            self.window.cursor_list.append(row)
            added += 1

        if added > 0:
            self.window.btn_convert.set_sensitive(True)
        if rejected:
            self._show_invalid_folders_dialog(rejected)

        return added

    def _folder_already_added(self, folder_path: str) -> bool:
        """Check if folder is already in the list."""
        return any(f.folder_path == folder_path for f in self.folder_rows)

    def _has_cursor_files(self, folder_path: str) -> bool:
        """Check if folder contains Windows cursor files."""
        cursor_extensions = {".cur", ".ani"}
        cursor_files = {"install.inf"}

        try:
            path = Path(folder_path)
            for item in path.iterdir():
                if item.suffix.lower() in cursor_extensions:
                    return True
                if item.name.lower() in cursor_files:
                    return True
        except Exception:
            pass

        return False

    def _show_invalid_folders_dialog(self, rejected: list[str]):
        rejected_list = "\n".join(f"• {name}" for name in rejected)

        dialog = Adw.AlertDialog(
            heading=_("No cursor files found"),
            body=f"{rejected_list}\n\n"
            f"{_('Expected *.cur, *.ani or install.inf inside the folder.')}",
        )
        dialog.add_response("ok", _("OK"))
        dialog.set_default_response("ok")
        dialog.present(self.window)

    def on_create_folder_row(self, row_name: str, row_folder_path: str):
        row = Adw.ActionRow(
            title=row_name,
            subtitle=row_folder_path,
            tooltip_text=row_folder_path,
        )
        folder_icon = Gtk.Image(icon_name="folder-symbolic")
        remove_btn = Gtk.Button(
            icon_name="user-trash-symbolic",
            tooltip_text=_("Remove"),
            valign=Gtk.Align.CENTER,
            css_classes=["flat"],
            cursor=Gdk.Cursor.new_from_name("pointer"),
        )

        status_stack = Gtk.Stack()
        status_stack.set_valign(Gtk.Align.CENTER)
        status_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        status_stack.set_transition_duration(300)

        spinner = Gtk.Spinner(spinning=False)

        check = Gtk.Image(icon_name="emblem-ok-symbolic")
        check.add_css_class("success")

        error = Gtk.Image(icon_name="dialog-error-symbolic")
        error.add_css_class("error")

        status_stack.add_named(spinner, "spinner")
        status_stack.add_named(check, "check")
        status_stack.add_named(error, "error")
        status_stack.set_visible_child_name("spinner")

        row_data = RowData(
            row_name=row_name,
            folder_path=row_folder_path,
            stack=status_stack,
            spinner=spinner,
        )
        remove_btn.connect("clicked", lambda _: self.on_remove_folder(row, row_data))
        self.folder_rows.append(row_data)
        row.add_prefix(folder_icon)
        row.add_suffix(status_stack)
        row.add_suffix(remove_btn)
        return row

    def on_remove_folder(self, row: Adw.ActionRow, row_data: RowData):
        self.window.cursor_list.remove(row)
        self.folder_rows.remove(row_data)
        is_converting = self.converter is not None and self.converter.is_running
        self.window.btn_convert.set_sensitive(len(self.folder_rows) > 0 and not is_converting)
        if is_converting:
            self.converter.remove(Path(row_data.folder_path))
            if len(self.folder_rows) == 0:
                self.converter.cancel()
        return True

    def setup_drop_target(self):
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_drop_folders)
        drop_target.connect("enter", self.on_drop_enter)
        drop_target.connect("leave", self.on_drop_leave)
        self.window.cursor_list.add_controller(drop_target)

    def on_drop_folders(self, target: Gtk.DropTarget, value: Gdk.FileList, x: int, y: int):
        folders = [
            (
                f.get_path(),
                f.query_info(
                    "standard::display-name", Gio.FileQueryInfoFlags.NONE, None
                ).get_display_name(),
            )
            for f in value.get_files()
            if f.query_info("standard::type", Gio.FileQueryInfoFlags.NONE, None).get_file_type()
            == Gio.FileType.DIRECTORY
        ]

        added = self._add_folders(folders)
        self.on_drop_leave(target)
        return added > 0

    def on_drop_enter(self, target, x, y):
        self.window.cursor_list.add_css_class("drop-target")
        return Gdk.DragAction.COPY

    def on_drop_leave(self, target):
        self.window.cursor_list.remove_css_class("drop-target")

    def setup_empty_state(self):
        self.window.cursor_list.set_placeholder(self.empty_status_page)
        click = Gtk.GestureClick()
        click.connect("pressed", self.on_empty_state_clicked)
        self.empty_status_page.add_controller(click)

    def on_empty_state_clicked(self, gesture: Gtk.GestureClick, x: float, y: float, _):
        if len(self.folder_rows) == 0:
            self.on_add_folders(None)

    def on_convert_files(self, _):
        print(f"converting files: {self.folder_rows}")

        # Check win2xcur before touching the UI state
        probe = CursorConverter(
            output_dir=Path("~").expanduser(),  # dummy, not used for the check
            on_progress=lambda _: None,
            on_all_done=lambda _: None,
        )
        if not probe.is_win2xcur_available():
            self._show_win2xcur_missing_dialog()
            return

        self.window.btn_convert.set_sensitive(False)
        self.window.btn_add.set_sensitive(False)
        self.window.btn_convert.set_child(Gtk.Spinner(spinning=True))
        self.converter = CursorConverter(
            output_dir=Path(self.settings.get_string("output-dir")).expanduser(),
            on_progress=self._on_conversion_progress,
            on_all_done=self._show_done_toast,
        )
        self.converter.add_many([Path(f.folder_path) for f in self.folder_rows])
        self.converter.start()

    def _show_win2xcur_missing_dialog(self):
        dialog = Adw.AlertDialog(
            heading=_("win2xcur Not Found"),
            body=_(
                "Flexa requires <b>win2xcur</b> to convert cursor files, "
                "but it could not be found on your system.\n\n"
                "Install it with:\n"
                "<tt>pip install win2xcur</tt>"
            ),
        )
        dialog.set_body_use_markup(True)
        dialog.add_response("close", _("Close"))
        dialog.add_response("docs", _("Open win2xcur page"))
        dialog.set_response_appearance("docs", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("close")
        dialog.connect("response", self._on_win2xcur_dialog_response)
        dialog.present(self.window)

    def _on_win2xcur_dialog_response(self, dialog, response_id):
        if response_id == "docs":
            launcher = Gtk.UriLauncher.new("https://github.com/quantum5/win2xcur")
            launcher.launch(self.window, None, None)

    def _on_conversion_progress(self, result: ConversionResult):
        file = next(
            (f for f in self.folder_rows if Path(f.folder_path) == result.folder_path),
            None,
        )
        if file is None:
            return
        match result.status:
            case ConversionStatus.RUNNING:
                file.spinner.set_spinning(True)
                file.stack.set_visible_child_name("spinner")
            case ConversionStatus.DONE:
                file.spinner.set_spinning(False)
                file.stack.set_visible_child_name("check")
            case ConversionStatus.CANCELED | ConversionStatus.ERROR:
                file.spinner.set_spinning(False)
                file.stack.set_visible_child_name("error")

    def _show_done_toast(self, results: list[ConversionResult]):
        self.window.btn_convert.set_sensitive(len(self.folder_rows) > 0)
        self.window.btn_convert.set_label(_("Convert"))
        self.window.btn_add.set_sensitive(True)

        if len(self.folder_rows) > 0 and results:
            done = sum(1 for r in results if r.status == ConversionStatus.DONE)
            total = len(results)
            toast = Adw.Toast(title=_("Conversion completed") + f" ({done}/{total})")
            toast.set_button_label(_("Open"))
            toast.connect("button-clicked", self.on_open_output_dir)
            self.window.toast_overlay.add_toast(toast)

    def on_open_output_dir(self, _toast):
        raw_output_path = self.converter.output_dir.parts
        output_path = GLib.build_filenamev(raw_output_path)
        file = Gio.File.new_for_path(output_path)
        launcher = Gtk.FileLauncher.new(file)
        try:
            launcher.launch(self.window, None, None)
        except GLib.GError:
            pass


def main(version):
    """The application's entry point."""
    app = FlexaApplication()
    return app.run(sys.argv)
