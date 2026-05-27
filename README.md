# Flexa

<div align="center">

![License](https://img.shields.io/badge/license-GPL--3.0--or--later-blue)
![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![GTK](https://img.shields.io/badge/GTK-4.10+-blue)
![LibAdwaita](https://img.shields.io/badge/LibAdwaita-1.5+-blue)
[![Flathub](https://img.shields.io/badge/Flathub-coming%20soon-yellow)](https://github.com/eucaue/flexa)

A simple GNOME app to convert Windows cursor themes to Linux format.

</div>

## Screenshots

<div align="center">

![Screenshot](./flexa.png)

</div>


## Features

- Add multiple cursor folders at once via the file picker
- Drag and drop cursor folders directly into the window
- Converts `.cur` and `.ani` cursors to PNG/XCursor format
- Saves to the configurable output directory (defaults to `~/.local/share/icons`)

## Requirements

- GTK 4.10+
- LibAdwaita 1.5+
- PyGObject
- Python 3.11+

## Installation

### From Flathub (coming soon)

```sh
flatpak install flathub io.github.eucaue.flexa
```

### Building with Flatpak

If you have `flatpak-builder` installed, this is the recommended way to build.

1. Install the GNOME SDK and Platform:
```sh
flatpak install flathub org.gnome.Sdk//50 org.gnome.Platform//50
```

2. Build and install locally:
```sh
flatpak-builder --user --install --force-clean _build io.github.eucaue.flexa.json
```

3. Run the app:
```sh
flatpak run io.github.eucaue.flexa
```

### Building from source

Make sure you have the dependencies installed:

```sh
# Fedora
sudo dnf install gtk4-devel libadwaita-devel gobject-introspection-devel meson ninja-build gettext python3-gobject
```

```sh
# Ubuntu / Debian
sudo apt install libgtk-4-dev libadwaita-1-dev libgirepository1.0-dev meson ninja-build gettext python3-gi
```

Then build:

```sh
meson setup build
meson compile -C build
sudo meson install -C build
```

## Usage

1. Click **+** in the header bar or drag and drop a cursor folder into the window
2. Add as many cursor themes as you want
3. Click **Convert**
4. A toast notification will appear when done — click **Open** to reveal the output folder

You can change the output directory in **Preferences**.

## Output

Converted cursors are saved to your configured output directory (default: `~/.local/share/icons`).

Each theme gets its own subfolder (named after the original folder). Apply the theme via **GNOME Tweaks** or **Settings → Appearance**.

## Contributing

Issues and pull requests are welcome at [github.com/eucaue/flexa](https://github.com/eucaue/flexa/issues).

## License

GPL-3.0-or-later
