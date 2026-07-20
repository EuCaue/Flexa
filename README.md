<div align="center">
<h1>Flexa</h1>
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
  <img src="https://img.shields.io/badge/version-1.2.0-blue" alt="Version" />
</a>
<a href="#">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python" />
</a>
<a href="#">
  <img src="https://img.shields.io/badge/LibAdwaita-1.5+-blue" alt="LibAdwaita" />
</a>
<br><br>
<p>Convert cursor themes between Windows and Linux.</p>

</div>

<div align="center">
<img alt="Flexa App" src="./flexa.png" style="max-width: 100%; height: auto;" />
</div>

## Features

- Convert cursor themes between Windows and Linux formats
- Convert `.cur` and `.ani` cursors to Linux format
- Convert Linux Xcursor themes to Windows format
- Add cursor folders manually or just drag them in
- Configurable output directories for both modes

## Installation

### Installing win2xcur

Flexa requires the `win2xcur` Python package to convert cursor files.

`win2xcur` requires [ImageMagick >= 7.0](https://imagemagick.org/script/download.php) for full cursor format support. Older versions may fail on some cursors.

**pipx:**

```sh
pipx install win2xcur
```

**pip:**

```sh
pip install --user win2xcur
```

**Using RPM (Fedora):**
If you download the RPM package from the [releases page](https://github.com/eucaue/flexa/releases/latest), you can install it using:

```sh
sudo dnf install ./python3-win2xcur-*.rpm
```

**Using DEB (Ubuntu/Debian):**
If you download the DEB package from the [releases page](https://github.com/eucaue/flexa/releases/latest), you can install it using:

```sh
sudo apt install ./python3-win2xcur_*.deb
sudo apt-get install -f -y
```

---

### From Flathub (coming soon)

```sh
flatpak install flathub io.github.eucaue.flexa
```

### From Release Page

Download the assets from the [latest release](https://github.com/eucaue/flexa/releases/latest).

**Windows:**

Download `Flexa-Windows-Installer.exe` and run it to install the application.

**Flatpak:**

```sh
flatpak install flexa.flatpak
```

**RPM (Fedora):**

```sh
sudo dnf install ./python3-win2xcur-*.rpm ./flexa-*.rpm
```

**DEB (Ubuntu/Debian):**

```sh
sudo apt install ./python3-win2xcur_*.deb ./flexa_*.deb
```

### Building with Flatpak

1. Install the GNOME SDK and Platform:

```sh
flatpak install flathub org.gnome.Sdk//50 org.gnome.Platform//50
```

2. Build and run:

<details>
<summary>Using <a href="https://just.systems"><code>just</code></a></summary>

```sh
just build-run
```

</details>

<details>
<summary>Manual Build</summary>

```sh
flatpak-builder --install --force-clean _build io.github.eucaue.flexa.json
flatpak run io.github.eucaue.flexa
```

</details>

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

<details>
<summary>Using <a href="https://just.systems"><code>just</code></a></summary>

```sh
just build-run-native
```

</details>

<details>
<summary>Manual Build</summary>

```sh
meson setup build
meson compile -C build
sudo meson install -C build
flexa
```

</details>

## Usage

Select the target mode (To Linux / To Windows), add cursor folders via **+** or drag-and-drop, then hit **Convert**. Output directories are configurable in **Preferences**.

### Output

Each theme is saved as its own subfolder (named after the source folder) inside your configured output directory. By default, this is `~/.local/share/icons` (when converting to Linux) and `~/Documents/Windows Cursors` (when converting to Windows). Defaults adjust on Windows.

## Contributing

Open an issue or PR at [github.com/eucaue/flexa](https://github.com/eucaue/flexa/issues).

## Acknowledgements

Built with:

- **[win2xcur](https://github.com/quantum5/win2xcur)**: Cursor conversion backend
- **[win-cursor-2-linux](https://github.com/lmezar/win-cursor-2-linux)**: Original inspiration

## License

GPL-3.0-or-later
