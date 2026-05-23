# Flexa

A simple GNOME app to convert Windows cursor themes to Linux format.

## Features

- Add multiple cursor folders at once
- Drag and drop support (TODO)
- Converts to the standard `~/.local/share/icons` directory (TODO)
- Toast notification with a link to the output folder when done (TODO)
- Follows the GNOME Human Interface Guidelines

## Requirements

- GNOME 45+
- GTK 4
- LibAdwaita 1.4+
- PyGObject

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

1. Click **+** in the header or drag and drop a cursor folder into the window
2. Add as many cursor themes as you want
3. Click **Convert**
4. A notification will appear when done — click it to open the output folder

## Output

Converted cursors are saved to:

`~/.local/share/icons/`

You can then apply the theme via **GNOME Tweaks** or **Settings → Appearance**.

## Contributing

Issues and pull requests are welcome at [github.com/eucaue/flexa](https://github.com/eucaue/flexa).

## License

GPL-3.0-or-later
