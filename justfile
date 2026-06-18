default:
    @just --list

# Build the flatpak application
build:
    flatpak-builder --user --force-clean _build io.github.eucaue.flexa.json

# Install the flatpak application
install:
    flatpak-builder --user --install --force-clean _build io.github.eucaue.flexa.json

# Run the installed flatpak application
run:
    flatpak run io.github.eucaue.flexa

# Run the installed flatpak application in Brazilian Portuguese
run-pt:
    flatpak run --env=LANGUAGE=pt_BR io.github.eucaue.flexa

# Build, install, and run the flatpak application
build-run: install run

# Build, install, and run the flatpak application in Brazilian Portuguese
build-run-pt: install run-pt

# Run without reinstalling (via flatpak-builder --run)
run-fast:
    flatpak-builder --run _build io.github.eucaue.flexa.json flexa

# Run without reinstalling in Brazilian Portuguese
run-fast-pt:
    flatpak-builder --run _build io.github.eucaue.flexa.json env LANGUAGE=pt_BR flexa

# Build natively
build-native:
    meson setup build --prefix="{{justfile_directory()}}/_native" --reconfigure 2>/dev/null || meson setup build --prefix="{{justfile_directory()}}/_native"
    meson compile -C build

# Install natively
install-native: build-native
    meson install -C build

# Run the installed native application
run-native:
    GSETTINGS_SCHEMA_DIR="{{justfile_directory()}}/_native/share/glib-2.0/schemas" "{{justfile_directory()}}/_native/bin/flexa"

# Run the installed native application in Brazilian Portuguese
run-native-pt:
    LANGUAGE=pt_BR GSETTINGS_SCHEMA_DIR="{{justfile_directory()}}/_native/share/glib-2.0/schemas" "{{justfile_directory()}}/_native/bin/flexa"

# Build, install, and run natively
build-run-native: install-native run-native

# Build, install, and run natively in Brazilian Portuguese
build-run-native-pt: install-native run-native-pt

# View application logs from journalctl
logs:
    journalctl --user -f -t io.github.eucaue.flexa

# Test Flatpak GitHub Action locally
act-flatpak:
    act -j flatpak --bind

# Test RPM GitHub Action locally
act-rpm:
    act -j rpm --bind

# Test DEB GitHub Action locally
act-deb:
    act -j deb --bind

# Clean build caches and directories
clean:
    rm -rf _build build .flatpak-builder _native dist
