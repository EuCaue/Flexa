# Flexa

<div align="center">

<a href="https://github.com/eucaue/flexa">
  <img src="https://img.shields.io/badge/Flathub-coming%20soon-yellow" alt="Flathub"/> 
</a>
<a href="#">
  <img src="https://img.shields.io/badge/license-GPL--3.0--or--later-blue" alt="License" /> 
</a>
<a href="#">
  <img src="https://img.shields.io/badge/GTK-4.10+-blue" alt="GTK" />
</a>
<a href="#">
  <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version" />
</a>
<a href="#">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python" />
</a>
<a href="#">
  <img src="https://img.shields.io/badge/LibAdwaita-1.5+-blue" alt="LibAdwaita" />
</a>

A simple GNOME app to convert Windows cursor themes to Linux format.

</div>

<div align="center">

![Screenshot](./flexa.png)

</div>

## Features

- Add multiple cursor folders at once via the file picker
- Drag and drop cursor folders directly into the window
- Converts `.cur` and `.ani` cursors to PNG/XCursor format
- Saves to the configurable output directory (defaults to `~/.local/share/icons`)

## Installation

### Installing win2xcur

Flexa requires the `win2xcur` command-line tool to convert cursor files.

**Using pipx (Recommended):**

```sh
pipx install win2xcur
```

**Using pip:**

```sh
pip install --user win2xcur
```

**Using RPM (Fedora):**
If you download the RPM package from the [releases page](https://github.com/eucaue/flexa/releases/latest), you can install it using:

```sh
sudo dnf install ./python3-win2xcur-*.rpm
```

---

### From Flathub (coming soon)

```sh
flatpak install flathub io.github.eucaue.flexa
```

### From Release Page

Download the assets from the [latest release](https://github.com/eucaue/flexa/releases/latest).

**Flatpak:**

```sh
flatpak install flexa.flatpak
```

**RPM (Fedora):**

```sh
sudo dnf install ./python3-win2xcur-*.rpm ./flexa-*.rpm
```

### Building with Flatpak

If you have `flatpak-builder` installed, this is the recommended way to build.

1. Install the GNOME SDK and Platform:

```sh
flatpak install flathub org.gnome.Sdk//50 org.gnome.Platform//50
```

2. Build and install locally:

```sh
flatpak-builder --install --force-clean _build io.github.eucaue.flexa.json
```

3. Run the app:

```sh
flatpak run io.github.eucaue.flexa
```

> **Note:** The Flatpak calls `win2xcur` on the host via `flatpak-spawn`, so `win2xcur` must still be installed on the host system (see [Installing win2xcur](#installing-win2xcur)).

### Building from source

## Requirements

- GTK 4.10+
- LibAdwaita 1.5+
- PyGObject
- Python 3.11+
- [win2xcur](https://github.com/quantum5/win2xcur) (see [Installing win2xcur](#installing-win2xcur))

```sh
# Fedora
sudo dnf install gtk4-devel libadwaita-devel gobject-introspection-devel meson ninja-build gettext python3-gobject
```

```sh
# Ubuntu / Debian
sudo apt install libgtk-4-dev libadwaita-1-dev libgirepository1.0-dev meson ninja-build gettext python3-gi libglib2.0-bin
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
4. A toast notification will appear when done, click **Open** to reveal the output folder

You can change the output directory in **Preferences**.

### Output

Converted cursors are saved to your configured output directory (default: `~/.local/share/icons`).

Each theme gets its own subfolder (named after the original folder).

## Contributing

Issues and pull requests are welcome at [github.com/eucaue/flexa](https://github.com/eucaue/flexa/issues).

## Acknowledgements

Flexa is built on top of and inspired by these projects:

- **[win2xcur](https://github.com/quantum5/win2xcur)**: The core engine used to convert Windows cursors.
- **[win-cursor-2-linux](https://github.com/lmezar/win-cursor-2-linux)**: The original script that inspired the idea

## License

GPL-3.0-or-later
