default:
    @just --list

# Build the flatpak application
build:
    flatpak-builder --ccache --user --force-clean _build io.github.eucaue.flexa.json

# Install the flatpak application
install:
    flatpak-builder --ccache --user --install --force-clean _build io.github.eucaue.flexa.json

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
    flatpak-builder --run _build io.github.eucaue.flexa.json env FLEXA_DEBUG=1 flexa

# Run without reinstalling in Brazilian Portuguese
run-fast-pt:
    flatpak-builder --run _build io.github.eucaue.flexa.json env FLEXA_DEBUG=1 LANGUAGE=pt_BR flexa

# Build natively
build-native:
    meson setup build --prefix="{{justfile_directory()}}/_native" --reconfigure 2>/dev/null || meson setup build --prefix="{{justfile_directory()}}/_native"
    meson compile -C build

# Install natively
install-native: build-native
    meson install -C build

# Run the installed native application (with debug enabled)
run-native:
    FLEXA_DEBUG=1 GSETTINGS_SCHEMA_DIR="{{justfile_directory()}}/_native/share/glib-2.0/schemas" "{{justfile_directory()}}/_native/bin/flexa"

# Run the installed native application in Brazilian Portuguese (with debug enabled)
run-native-pt:
    FLEXA_DEBUG=1 LANGUAGE=pt_BR GSETTINGS_SCHEMA_DIR="{{justfile_directory()}}/_native/share/glib-2.0/schemas" "{{justfile_directory()}}/_native/bin/flexa"

# Build, install, and run natively
build-run-native: install-native run-native

# Build, install, and run natively in Brazilian Portuguese
build-run-native-pt: install-native run-native-pt

# View application logs from journalctl
logs:
    journalctl --user -f -t io.github.eucaue.flexa

# Test Flatpak GitHub Action locally
act-flatpak:
    act -W .github/workflows/build-flatpak.yml -j flatpak --bind

# Test RPM GitHub Action locally
act-rpm:
    act -W .github/workflows/build-rpm.yml -j rpm --bind

# Test DEB GitHub Action locally
act-deb:
    act -W .github/workflows/build-deb.yml -j deb --bind

# Lint flatpak manifest via flathub container
lint-manifest:
    mkdir -p /tmp/opencode/lintwork && cp io.github.eucaue.flexa.json /tmp/opencode/lintwork/
    podman run --rm -v "/tmp/opencode/lintwork:/work:U" -v "{{justfile_directory()}}/packaging/flathub/exceptions.json:/exceptions.json:ro" -w /work ghcr.io/flathub-infra/flatpak-builder-lint:unprivileged --exceptions --user-exceptions /exceptions.json manifest io.github.eucaue.flexa.json; status=$?; podman unshare chown -R 0:0 /tmp/opencode/lintwork; exit $status

# Lint exported ostree repo via flathub container (run after build with --repo=repo)
# appstream-external-screenshot-url is expected locally: Flathub CI mirrors screenshots
lint-repo:
    podman run --rm -v "{{justfile_directory()}}/repo:/work:U" -v "{{justfile_directory()}}/packaging/flathub/exceptions.json:/exceptions.json:ro" -w /work ghcr.io/flathub-infra/flatpak-builder-lint:unprivileged --exceptions --user-exceptions /exceptions.json repo /work; status=$?; podman unshare chown -R 0:0 "{{justfile_directory()}}/repo"; exit $status

# Generate the Flathub manifest from a pushed release tag (e.g. just flathub-manifest v1.2.2)
flathub-manifest tag:
    git ls-remote --exit-code --tags origin "refs/tags/{{tag}}" > /dev/null
    mkdir -p dist/flathub
    jq --arg tag "{{tag}}" --arg commit "$(git rev-list -n1 '{{tag}}')" \
        '(.modules[] | select(.name == "flexa") | .sources) = [{"type": "git", "url": "https://github.com/eucaue/flexa.git", "tag": $tag, "commit": $commit}]' \
        io.github.eucaue.flexa.json > dist/flathub/io.github.eucaue.flexa.json

# Clean build caches and directories
clean:
    rm -rf _build build .flatpak-builder _native dist

# Run code linters (ruff and pyright)
lint:
    uv run ruff check .
    uv run pyright src

# Auto-fix lint errors and format code
format:
    uv run ruff check --fix .
    uv run ruff format .

