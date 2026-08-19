# window.py
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

from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/io/github/eucaue/flexa/window.ui")
class FlexaWindow(Adw.ApplicationWindow):
    """Main application window for Flexa."""

    __gtype_name__ = "FlexaWindow"

    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    view_stack: Adw.ViewStack = Gtk.Template.Child()
    view_switcher_bar: Adw.ViewSwitcherBar = Gtk.Template.Child()

    cursor_list_to_linux: Gtk.ListBox = Gtk.Template.Child()
    btn_convert_to_linux: Gtk.Button = Gtk.Template.Child()

    cursor_list_to_windows: Gtk.ListBox = Gtk.Template.Child()
    btn_convert_to_windows: Gtk.Button = Gtk.Template.Child()

    btn_add: Gtk.Button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
