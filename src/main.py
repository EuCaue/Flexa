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

from typing import TypedDict

from gi.repository import Adw, Gdk, Gio, Gtk

from .window import FlexaWindow


class RowData(TypedDict):
    row_name: str
    folder_path: str


class FlexaApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id="io.github.eucaue.flexa",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            resource_base_path="/io/github/eucaue/flexa",
        )
        self.create_action("quit", lambda *_: self.quit(), ["<control>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)
        self.create_action("shortcuts", self.on_shortcuts_action)
        self.files: list[RowData] = []
        self.filesDialog: Gtk.FileDialog = Gtk.FileDialog()
        self.empty_state: Adw.StatusPage = Adw.StatusPage(
            title="No Folders Added",
            description="Drag folders here or click the button below",
            icon_name="folder-symbolic",
        )
        self.window = None

    def connect_signals(self):
        self.window.btn_add.connect("clicked", self.on_add_folders)
        self.window.btn_convert.connect("clicked", self.on_convert_files)
        self.setup_drop_target()
        self.window.cursor_list.set_placeholder(self.empty_state)

    def setup_drop_target(self):
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_drop_folders)
        drop_target.connect("enter", self.on_drop_enter)
        drop_target.connect("leave", self.on_drop_leave)
        self.window.cursor_list.add_controller(drop_target)

    def on_drop_folders(
        self, target: Gtk.DropTarget, value: Gdk.FileList, x: int, y: int
    ):
        files = value.get_files()  # files dragged
        added = 0

        for gfile in files:
            try:
                info = gfile.query_info(
                    "standard::type,standard::display-name",
                    Gio.FileQueryInfoFlags.NONE,
                    None,
                )
                # accept only directories
                if info.get_file_type() != Gio.FileType.DIRECTORY:
                    continue

                folder_path = gfile.get_path()
                folder_name = info.get_display_name()

                # avoid duplicates
                if any(f["folder_path"] == folder_path for f in self.files):
                    continue

                row = self.on_create_folder_row(folder_name, folder_path)
                self.window.cursor_list.append(row)
                added += 1

            except Exception as e:
                print(f"Error while processing file: {e}")

        if added > 0:
            self.window.btn_convert.set_sensitive(True)

        self.on_drop_leave(target)
        return added > 0  # reject visually if no folders were added

    def on_drop_enter(self, target, x, y):
        self.window.cursor_list.add_css_class("drop-target")
        return Gdk.DragAction.COPY

    def on_drop_leave(self, target):
        self.window.cursor_list.remove_css_class("drop-target")

    def on_convert_files(self, _):
        print(f"converting files: {self.files}")
        for file in self.files:
            print(f"converting file: {file}")

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

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name="Flexa",
            application_icon="io.github.eucaue.flexa",
            developer_name="caue",
            version="0.1.0",
            # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
            translator_credits=_("translator-credits"),
            developers=["caue"],
            copyright="© 2026 caue",
        )
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        print("app.preferences action activated")

    # TODO: OPEN FILE DIALOG AND ADD FILES
    def on_add_folders(self, widget):
        """Callback for the app.add_files action."""
        print("Opened dialog")
        # TODO: filter files by folders
        self.filesDialog.set_title("Select cursor folders")
        self.filesDialog.select_multiple_folders(
            self.window, None, self.on_select_folders, None
        )

    def on_select_folders(self, dialog, result, _):
        folders: Gtk.ListStore = dialog.select_multiple_folders_finish(result)
        print(f"folders: {folders}")
        if folders is not None:
            for i in range(folders.get_n_items()):
                # TODO: selected file: /run/user/1000/doc/2c0a20f7/wall.excalidraw
                # check if i can really use this.
                folder = folders.get_item(i)
                folder_path = folder.get_path()
                folder_name = folder.get_basename()
                print(f"selected folder: {folder_path}")
                row = self.on_create_folder_row(folder_name, folder_path)
                self.window.cursor_list.append(row)
                self.window.btn_convert.set_sensitive(True)

    def on_remove_folder(self, row: Adw.ActionRow, row_name: str, folder_path: str):
        print(f"removing folder: {row_name}")
        self.window.cursor_list.remove(row)
        self.files.remove({"row_name": row_name, "folder_path": folder_path})
        return True

    def on_create_folder_row(self, row_name: str, row_folder_path: str):
        row = Adw.ActionRow(
            title=row_name,
            subtitle=row_folder_path,
        )
        folder_icon = Gtk.Image(icon_name="folder-symbolic")
        remove_btn = Gtk.Button(
            icon_name="user-trash-symbolic",
            tooltip_text=_("Remove"),
            valign=Gtk.Align.CENTER,
            css_classes=["flat"],
            cursor=Gdk.Cursor.new_from_name("pointer"),
        )
        remove_btn.connect(
            "clicked", lambda _: self.on_remove_folder(row, row_name, row_folder_path)
        )
        self.files.append({"row_name": row_name, "folder_path": row_folder_path})
        row.add_prefix(folder_icon)
        row.add_suffix(remove_btn)
        return row

    def on_shortcuts_action(self, widget, _):
        print("app shortcuts called...")
        builder = Gtk.Builder.new_from_resource(
            "/io/github/eucaue/flexa/shortcuts-dialog.ui"
        )
        dialog = builder.get_object("shortcuts_dialog")
        dialog.present(self.props.active_window)

    def create_action(self, name, callback, shortcuts=None):
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


def main(version):
    """The application's entry point."""
    app = FlexaApplication()
    return app.run(sys.argv)
