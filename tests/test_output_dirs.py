# test_output_dirs.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

# GLib caches user dirs per process, so every case needs a fresh interpreter.
_PRELUDE = f"""
import sys, types
from pathlib import Path

pkg = types.ModuleType("flexa")
pkg.__path__ = [{str(SRC_DIR)!r}]
sys.modules["flexa"] = pkg

# main.py imports the template-backed preferences dialog, which needs the
# compiled GResource. Stub those two modules so _default_output_dir is real.
prefs = types.ModuleType("flexa.preferences")
prefs.FallbackScan = object
prefs.FlexaPreferencesDialog = object
sys.modules["flexa.preferences"] = prefs
window = types.ModuleType("flexa.window")
window.FlexaWindow = object
sys.modules["flexa.window"] = window
"""


def _fake_home(tmp_path: Path, documents: str | None) -> Path:
    config = tmp_path / ".config"
    config.mkdir()
    if documents is not None:
        (config / "user-dirs.dirs").write_text(f'XDG_DOCUMENTS_DIR="$HOME/{documents}"\n')
    return tmp_path


def _run(home: Path, code: str) -> str:
    env = {
        **os.environ,
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
    }
    env.pop("XDG_DOCUMENTS_DIR", None)
    result = subprocess.run(
        [sys.executable, "-c", _PRELUDE + code],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _documents_dir(home: Path, in_flatpak: bool) -> str:
    # The module-level constant is computed at import; pin it for the test.
    return _run(
        home,
        "import flexa.cursor_converter as cc\n"
        f"cc._IN_FLATPAK = {in_flatpak}\n"
        "print(cc.documents_dir())",
    )


def test_documents_dir_honors_xdg_documents_dir(tmp_path):
    home = _fake_home(tmp_path, "Documentos")
    assert _documents_dir(home, in_flatpak=True) == str(home / "Documentos")


def test_documents_dir_falls_back_native_without_xdg_dir(tmp_path):
    home = _fake_home(tmp_path, None)
    assert _documents_dir(home, in_flatpak=False) == str(home / "Documents")


def test_documents_dir_none_in_flatpak_without_xdg_dir(tmp_path):
    home = _fake_home(tmp_path, None)
    assert _documents_dir(home, in_flatpak=True) == "None"


def test_default_windows_output_uses_documents_dir(tmp_path):
    home = _fake_home(tmp_path, "Documentos")
    output = _run(
        home,
        "import flexa.cursor_converter as cc\n"
        "cc._IN_FLATPAK = True\n"
        "from flexa.main import _default_output_dir\n"
        "print(_default_output_dir('output-dir-windows'))",
    )
    assert output == str(home / "Documentos" / "Windows Cursors")


def test_default_windows_output_is_none_in_flatpak_without_xdg_dir(tmp_path):
    home = _fake_home(tmp_path, None)
    output = _run(
        home,
        "import flexa.cursor_converter as cc\n"
        "cc._IN_FLATPAK = True\n"
        "from flexa.main import _default_output_dir\n"
        "print(_default_output_dir('output-dir-windows'))",
    )
    assert output == "None"


def test_validate_output_dir_accepts_writable_dir(tmp_path):
    target = tmp_path / "ok"
    output = _run(
        tmp_path,
        "from pathlib import Path\n"
        "from flexa.main import _validate_output_dir\n"
        f"print(_validate_output_dir(Path({str(target)!r})) is None)",
    )
    assert output == "True"


def test_validate_output_dir_reports_failure(tmp_path):
    blocked = tmp_path / "regular-file"
    blocked.write_text("not a directory")
    error = _run(
        tmp_path,
        "from pathlib import Path\n"
        "from flexa.main import _validate_output_dir\n"
        f"print(_validate_output_dir(Path({str(blocked / 'sub')!r})) is not None)",
    )
    assert error == "True"


def test_no_hardcoded_documents_literal():
    # cursor_converter.py holds the documented native fallback.
    patterns = (
        '"~/Documents',
        "'~/Documents",
        'Path.home() / "Documents"',
        "Path.home() / 'Documents'",
    )
    offenders = [
        path.name
        for path in SRC_DIR.glob("*.py")
        if path.name != "cursor_converter.py"
        and any(pattern in path.read_text() for pattern in patterns)
    ]
    assert offenders == []
