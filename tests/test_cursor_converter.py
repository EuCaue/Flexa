# test_cursor_converter.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import types
from pathlib import Path

# Ensure 'flexa' package can be imported from 'src'
_SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if "flexa" not in sys.modules:
    _pkg = types.ModuleType("flexa")
    _pkg.__path__ = [str(_SRC_DIR)]
    sys.modules["flexa"] = _pkg

from flexa.cursor_converter import CursorConverter, host_path  # noqa: E402


def _make_converter(output_dir: Path) -> CursorConverter:
    return CursorConverter(
        output_dir=output_dir,
        on_progress=lambda _: None,
        on_all_done=lambda _: None,
    )


def test_parse_inf_maps_aliases_and_ignores_unknown_keys(tmp_path: Path) -> None:
    inf_file = tmp_path / "install.inf"
    inf_file.write_text(
        """
[Version]
signature="$CHICAGO$"

[Strings]
; standard pointer with comments
pointer = "arrow.cur" ; main pointer
; known alias with quoted name and semicolon inside quotes
working = "busy;spinner.ani" ; working alias
; case-insensitive alias
AppStarting = normal_work.ani
; unknown key should be ignored
unknown_key = "ignore.cur"
        """.strip(),
        encoding="utf-8",
    )

    converter = _make_converter(tmp_path)
    mapping = converter._parse_inf(inf_file)

    assert "arrow.cur" in mapping
    assert "arrow" in mapping["arrow.cur"]
    assert "default" in mapping["arrow.cur"]

    assert "busy;spinner.ani" in mapping
    assert "left_ptr_watch" in mapping["busy;spinner.ani"]

    assert "normal_work.ani" in mapping
    assert "progress" in mapping["normal_work.ani"]

    assert "ignore.cur" not in mapping


def test_map_by_filename_accepts_cursor_extensions_case_insensitively(tmp_path: Path) -> None:
    folder = tmp_path / "theme"
    folder.mkdir()
    (folder / "Arrow.CUR").touch()
    (folder / "wait.Ani").touch()
    (folder / "custom.cur").touch()
    (folder / "readme.TXT").touch()
    (folder / "preview.png").touch()

    converter = _make_converter(tmp_path)
    mapping = converter._map_by_filename(folder)

    assert "Arrow.CUR" in mapping
    assert "arrow" in mapping["Arrow.CUR"]

    assert "wait.Ani" in mapping
    assert "wait" in mapping["wait.Ani"]

    assert "custom.cur" in mapping
    assert mapping["custom.cur"] == ["custom"]

    assert "readme.TXT" not in mapping
    assert "preview.png" not in mapping


def test_linux_fallback_validation_accepts_direct_and_nested_cursors(tmp_path: Path) -> None:
    # Direct folder with extensionless cursor files
    direct = tmp_path / "direct_theme"
    direct.mkdir()
    (direct / "arrow").touch()
    assert CursorConverter.is_valid_fallback_path(direct) is True

    # Nested cursors/ folder with extensionless cursor files
    nested = tmp_path / "nested_theme"
    cursors_dir = nested / "cursors"
    cursors_dir.mkdir(parents=True)
    (cursors_dir / "arrow").touch()
    assert CursorConverter.is_valid_fallback_path(nested) is True


def test_fallback_validation_rejects_empty_directories(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty_theme"
    empty_dir.mkdir()
    assert CursorConverter.is_valid_fallback_path(empty_dir) is False

    empty_nested = tmp_path / "empty_nested_theme"
    (empty_nested / "cursors").mkdir(parents=True)
    assert CursorConverter.is_valid_fallback_path(empty_nested) is False

    only_extensions = tmp_path / "only_extensions_theme"
    only_extensions.mkdir()
    (only_extensions / "arrow.png").touch()
    assert CursorConverter.is_valid_fallback_path(only_extensions) is False


def test_linux_fallback_copy_preserves_existing_files(tmp_path: Path) -> None:
    fallback = tmp_path / "fallback"
    fallback_cursors = fallback / "cursors"
    fallback_cursors.mkdir(parents=True)

    # Fallback cursors
    (fallback_cursors / "arrow").write_text("fallback_arrow", encoding="utf-8")
    (fallback_cursors / "cross").write_text("fallback_cross", encoding="utf-8")
    (fallback_cursors / "notes.txt").write_text("irrelevant", encoding="utf-8")
    (fallback_cursors / "nested_dir").mkdir()

    # Destination cursors dir
    dest_cursors = tmp_path / "dest" / "cursors"
    dest_cursors.mkdir(parents=True)
    (dest_cursors / "arrow").write_text("existing_arrow", encoding="utf-8")

    converter = _make_converter(tmp_path)
    converter._copy_missing_linux_cursors(fallback, dest_cursors)

    # Existing file must be preserved
    assert (dest_cursors / "arrow").read_text(encoding="utf-8") == "existing_arrow"
    # Missing cursor must be copied
    assert (dest_cursors / "cross").read_text(encoding="utf-8") == "fallback_cross"
    # Irrelevant files must not be copied
    assert not (dest_cursors / "notes.txt").exists()
    assert not (dest_cursors / "nested_dir").exists()


def test_host_path_maps_known_sandbox_icon_paths() -> None:
    # Known sandbox path mapping
    assert (
        host_path("/run/host/share/icons/Adwaita")
        == "/usr/share/icons/Adwaita"
    )
    assert (
        host_path("/run/host/share/icons")
        == "/usr/share/icons"
    )

    # Unrelated path should remain unchanged
    assert (
        host_path("/home/caue/custom/icons")
        == "/home/caue/custom/icons"
    )
