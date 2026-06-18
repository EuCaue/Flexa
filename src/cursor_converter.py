# cursor_converter.py

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Callable

import gi

gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio, GLib


class ConversionStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    DONE = auto()
    ERROR = auto()
    CANCELED = auto()


@dataclass
class ConversionResult:
    folder_name: str
    folder_path: Path
    output_path: Path | None
    status: ConversionStatus
    error: str | None = None


OnProgressCallback = Callable[[ConversionResult], None]
OnAllDoneCallback = Callable[[list[ConversionResult]], None]


_INF_KEY_TO_LINUX: dict[str, list[str]] = {
    "pointer": ["arrow", "default", "left_ptr", "top_left_arrow"],
    "help": ["help", "left_ptr_help", "question_arrow", "whats_this"],
    "work": ["left_ptr_watch", "progress", "pirate"],
    "busy": ["wait", "watch", "half-busy"],
    "cross": ["cross", "crosshair"],
    "text": ["ibeam", "text", "xterm"],
    "hand": ["draft", "pencil"],
    "unavailable": ["circle", "crossed_circle", "forbidden", "no_drop", "not_allowed"],
    "vert": [
        "ns-resize",
        "n-resize",
        "s-resize",
        "v_double_arrow",
        "size_ver",
        "row-resize",
    ],
    "horz": [
        "ew-resize",
        "e-resize",
        "w-resize",
        "h_double_arrow",
        "size_hor",
        "col-resize",
    ],
    "dgn1": ["nwse-resize", "nw-resize", "se-resize", "size_fdiag"],
    "dgn2": ["nesw-resize", "ne-resize", "sw-resize", "size_bdiag"],
    "move": [
        "fleur",
        "move",
        "size_all",
        "all-scroll",
        "grabbing",
        "closedhand",
        "dnd-move",
    ],
    "alternate": ["up_arrow", "center_ptr"],
    "link": ["pointer", "hand", "hand1", "hand2", "grab", "openhand", "pointing_hand"],
    "pin": ["cell", "plus"],
    "person": ["context-menu"],
}

_FILENAME_TO_LINUX: dict[str, list[str]] = {
    "arrow": _INF_KEY_TO_LINUX["pointer"],
    "default": _INF_KEY_TO_LINUX["pointer"],
    "normal": _INF_KEY_TO_LINUX["pointer"],
    "help": _INF_KEY_TO_LINUX["help"],
    "appstarting": _INF_KEY_TO_LINUX["work"],
    "work": _INF_KEY_TO_LINUX["work"],
    "wait": _INF_KEY_TO_LINUX["busy"],
    "busy": _INF_KEY_TO_LINUX["busy"],
    "crosshair": _INF_KEY_TO_LINUX["cross"],
    "cross": _INF_KEY_TO_LINUX["cross"],
    "ibeam": _INF_KEY_TO_LINUX["text"],
    "beam": _INF_KEY_TO_LINUX["text"],
    "text": _INF_KEY_TO_LINUX["text"],
    "nwpen": _INF_KEY_TO_LINUX["hand"],
    "pencil": _INF_KEY_TO_LINUX["hand"],
    "no": _INF_KEY_TO_LINUX["unavailable"],
    "unavailable": _INF_KEY_TO_LINUX["unavailable"],
    "sizens": _INF_KEY_TO_LINUX["vert"],
    "sizewe": _INF_KEY_TO_LINUX["horz"],
    "sizenwse": _INF_KEY_TO_LINUX["dgn1"],
    "sizenesw": _INF_KEY_TO_LINUX["dgn2"],
    "sizeall": _INF_KEY_TO_LINUX["move"],
    "move": _INF_KEY_TO_LINUX["move"],
    "uparrow": _INF_KEY_TO_LINUX["alternate"],
    "hand": _INF_KEY_TO_LINUX["link"],
    "link": _INF_KEY_TO_LINUX["link"],
    "pin": _INF_KEY_TO_LINUX["pin"],
    "person": _INF_KEY_TO_LINUX["person"],
}

_INF_KEY_ALIASES: dict[str, str] = {
    "appstarting": "work",
    "arrow": "pointer",
    "beam": "text",
    "crosshair": "cross",
    "default": "pointer",
    "handwriting": "hand",
    "ibeam": "text",
    "normal": "pointer",
    "nwpen": "hand",
    "precision": "cross",
    "sizenesw": "dgn2",
    "sizens": "vert",
    "sizeall": "move",
    "sizenwse": "dgn1",
    "sizewe": "horz",
    "uparrow": "alternate",
    "wait": "busy",
    "working": "work",
}


@dataclass
class CursorConverter:
    """
    Converts Windows cursor folders to Linux using Gio.Task and
    Gio.Subprocess — native GLib APIs, without manual threading.

    - Gio.Task:       runs work in a GLib thread pool, calls callback
                      on the main loop automatically (without manual idle_add)
    - Gio.Subprocess: asynchronous process, does not block any thread
    - Gio.Cancellable: cooperative cancellation propagated to subprocesses

    Usage:
        converter = CursorConverter(
            output_dir=Path("~/.icons").expanduser(),
            on_progress=lambda r: update_ui(r),
            on_all_done=lambda results: show_toast(results),
        )
        converter.add_many([Path("/tmp/MyCursor")])
        converter.start()

        # To cancel:
        converter.cancel()
    """

    output_dir: Path
    on_progress: OnProgressCallback
    on_all_done: OnAllDoneCallback
    win2xcur_bin: str = "win2xcur"

    # Shared Cancellable among all session subprocesses
    _cancellable: Gio.Cancellable = field(default_factory=Gio.Cancellable, init=False, repr=False)
    _folders: list[Path] = field(default_factory=list, init=False, repr=False)
    _results: list[ConversionResult] = field(default_factory=list, init=False, repr=False)
    _skipped: set[Path] = field(default_factory=set, init=False, repr=False)
    _cancellables: dict[Path, Gio.Cancellable] = field(default_factory=dict, init=False, repr=False)
    _is_running: bool = field(default=False, init=False, repr=False)

    @property
    def is_running(self) -> bool:
        return self._is_running

    def add(self, folder: Path) -> None:
        self._folders.append(folder)

    def add_many(self, folders: list[Path]) -> None:
        self._folders.extend(folders)

    def is_win2xcur_available(self) -> bool:
        """Returns True if the win2xcur binary can be located on the system."""
        try:
            self._resolve_win2xcur_command()
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def get_imagemagick_version() -> tuple[int, int, int] | None:
        """Returns (major, minor, patch) or None if ImageMagick is not found."""
        for cmd in ("magick", "convert"):
            try:
                result = subprocess.run(
                    [cmd, "-version"],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode != 0:
                    continue
                match = re.search(r"ImageMagick (\d+)\.(\d+)\.(\d+)", result.stdout)
                if match:
                    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                continue
        return None

    @staticmethod
    def is_imagemagick_supported() -> bool:
        """Returns True if ImageMagick >= 7.0 is available."""
        version = CursorConverter.get_imagemagick_version()
        return version is not None and version >= (7, 0, 0)

    def start(self) -> None:
        """Starts the conversion. Non-blocking — returns immediately."""
        self._is_running = True
        self._cancellable.reset()
        self._results.clear()
        self._skipped.clear()
        self._cancellables.clear()
        self._process_next(0)

    def cancel(self) -> None:
        """Cancels the ongoing conversion, including subprocesses."""
        self._cancellable.cancel()
        for cancellable in self._cancellables.values():
            cancellable.cancel()

    def remove(self, folder: Path) -> None:
        """Removes a folder from the conversion queue."""
        self._skipped.add(folder)
        cancellable = self._cancellables.get(folder)
        if cancellable:
            cancellable.cancel()

    def _process_next(self, index: int) -> None:
        """
        Starts the conversion of item `index` via Gio.Task.
        When it finishes, the callback schedules the next one — asynchronous recursion.
        """
        if index >= len(self._folders):
            self._is_running = False
            self.on_all_done(list(self._results))
            return

        if self._cancellable.is_cancelled():
            self._is_running = False
            self.on_all_done(list(self._results))
            return

        folder = self._folders[index]

        if folder in self._skipped:
            self._process_next(index + 1)
            return

        # Emits RUNNING on the main loop (Gio.Task callbacks always run on the main loop)
        self.on_progress(
            ConversionResult(
                folder_name=folder.name,
                folder_path=folder,
                output_path=self.output_dir / folder.name,
                status=ConversionStatus.RUNNING,
            )
        )

        folder_cancellable = Gio.Cancellable.new()
        self._cancellables[folder] = folder_cancellable

        # If the session cancellable is already cancelled, cancel this one too
        if self._cancellable.is_cancelled():
            folder_cancellable.cancel()

        task = Gio.Task.new(
            None,  # source_object (no owner GObject)
            folder_cancellable,  # propagated cancellable
            self._on_task_done,  # callback on the main loop
            index,  # task_data passed to the callback
        )
        # NOTE: do NOT touch GTK widgets inside this function
        task.run_in_thread(lambda task, _, __, ___: self._worker(task, folder))

    def _on_task_done(
        self,
        _source: None,
        task: Gio.Task,
        index: int,
    ) -> None:
        """
        Called automatically on the main loop by GLib when the task finishes.
        Does not need GLib.idle_add — Gio.Task already ensures this.
        """
        folder = self._folders[index]
        self._cancellables.pop(folder, None)

        try:
            # task.propagate_value() raises GLib.Error if there was an error or cancellation
            ok, result = task.propagate_value()
            if ok:
                self._results.append(result)
                self.on_progress(result)
        except GLib.Error as err:
            if self._cancellable.is_cancelled():
                self._is_running = False
                canceled = ConversionResult(
                    folder_name=folder.name,
                    folder_path=folder,
                    output_path=None,
                    status=ConversionStatus.CANCELED,
                )
                self._results.append(canceled)
                self.on_progress(canceled)
                self.on_all_done(list(self._results))
                return

            cancellable = task.get_cancellable()
            if cancellable and cancellable.is_cancelled():
                canceled = ConversionResult(
                    folder_name=folder.name,
                    folder_path=folder,
                    output_path=None,
                    status=ConversionStatus.CANCELED,
                )
                self.on_progress(canceled)
            else:
                error_result = ConversionResult(
                    folder_name=folder.name,
                    folder_path=folder,
                    output_path=None,
                    status=ConversionStatus.ERROR,
                    error=err.message,
                )
                self._results.append(error_result)
                self.on_progress(error_result)

        # Schedules the next item
        self._process_next(index + 1)

    def _worker(self, task: Gio.Task, folder: Path) -> None:
        """
        Runs in a separate thread (GLib pool).
        Does not touch widgets. Communicates result via task.return_value().
        """
        theme_name = folder.name
        out_theme = self.output_dir / theme_name
        cursors_dir = out_theme / "cursors"
        cancellable = task.get_cancellable()

        try:
            if cancellable and cancellable.is_cancelled():
                task.return_error(GLib.Error("Cancelled"))
                return

            cursors_dir.mkdir(parents=True, exist_ok=True)
            mapping = self._build_mapping(folder)
            self._run_win2xcur_sync(folder, cursors_dir, mapping, cancellable)
            self._write_index_theme(out_theme, theme_name)

            result = ConversionResult(
                folder_name=theme_name,
                folder_path=folder,
                output_path=out_theme,
                status=ConversionStatus.DONE,
            )
            task.return_value(result)

        except Exception as exc:
            if cancellable and cancellable.is_cancelled():
                task.return_error(GLib.Error("Cancelled"))
            else:
                self._write_error_log(out_theme, exc)
                task.return_error(GLib.Error(str(exc)))

    def _run_win2xcur_sync(
        self,
        source_dir: Path,
        cursors_dir: Path,
        mapping: dict[str, list[str]],
        cancellable: Gio.Cancellable | None,
    ) -> None:
        """
        Calls win2xcur for each file via Gio.Subprocess.
        Since we are in a worker thread, we use communicate() which blocks
        the thread (not the main loop).
        """
        win2xcur_cmd = self._resolve_win2xcur_command()

        for win_filename, linux_names in mapping.items():
            if cancellable and cancellable.is_cancelled():
                return

            src_file = source_dir / win_filename
            if not src_file.exists():
                continue

            primary_name = linux_names[0]
            out_file = cursors_dir / primary_name

            with tempfile.TemporaryDirectory(dir=cursors_dir) as temp_dir:
                launcher = Gio.SubprocessLauncher.new(
                    Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE
                )
                proc = launcher.spawnv([*win2xcur_cmd, str(src_file), "-o", temp_dir])

                ok, _stdout, stderr_bytes = proc.communicate(None, cancellable)

                if not ok or proc.get_exit_status() != 0:
                    stderr = (
                        stderr_bytes.get_data().decode(errors="replace") if stderr_bytes else ""
                    )
                    raise RuntimeError(f"win2xcur failed for {src_file.name}: {stderr}")

                generated = Path(temp_dir) / src_file.stem
                if not generated.exists():
                    raise FileNotFoundError(f"win2xcur did not produce output for {src_file.name}")

                shutil.move(str(generated), str(out_file))

            for alias in linux_names[1:]:
                link = cursors_dir / alias
                if not link.exists():
                    link.symlink_to(primary_name)

    def _resolve_win2xcur_command(self) -> list[str]:
        resolved = shutil.which(self.win2xcur_bin)
        if resolved:
            return [resolved]
        for candidate in self._candidate_paths():
            if Path(candidate).is_file():
                return [candidate]
        raise FileNotFoundError(
            "win2xcur not found. Checked:\n" + "\n".join(self._candidate_paths())
        )

    def _candidate_paths(self) -> list[str]:
        path_dirs = [e for e in os.environ.get("PATH", "").split(":") if e]
        seen: set[str] = set()
        result: list[str] = []
        for entry in [*path_dirs, str(Path("~/.local/bin").expanduser())]:
            candidate = str(Path(entry) / self.win2xcur_bin)
            if candidate not in seen:
                seen.add(candidate)
                result.append(candidate)
        return result

    def _build_mapping(self, folder: Path) -> dict[str, list[str]]:
        inf = next((f for f in folder.iterdir() if f.suffix.lower() == ".inf"), None)
        return self._parse_inf(inf) if inf else self._map_by_filename(folder)

    def _parse_inf(self, inf: Path) -> dict[str, list[str]]:
        strings = self._parse_inf_strings(inf)
        mapping: dict[str, list[str]] = {}
        for inf_key, value in strings.items():
            canonical = _INF_KEY_ALIASES.get(inf_key, inf_key)
            linux_names = _INF_KEY_TO_LINUX.get(canonical)
            if not linux_names:
                continue
            filename = value.strip().strip('"')
            if filename:
                mapping.setdefault(filename, []).extend(linux_names)
        return mapping

    def _parse_inf_strings(self, inf: Path) -> dict[str, str]:
        content = inf.read_text(encoding="utf-8", errors="ignore")
        section = self._extract_section(content, "strings")
        strings: dict[str, str] = {}
        for raw in section:
            line = self._strip_comment(raw).strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().lower()
            value = value.strip()
            if key and value:
                strings[key] = value
        return strings

    def _extract_section(self, content: str, name: str) -> list[str]:
        lines: list[str] = []
        inside = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                inside = stripped[1:-1].strip().lower() == name.lower()
                continue
            if inside:
                lines.append(line)
        return lines

    def _strip_comment(self, line: str) -> str:
        in_quotes = False
        for i, ch in enumerate(line):
            if ch == '"':
                in_quotes = not in_quotes
            elif ch == ";" and not in_quotes:
                return line[:i]
        return line

    def _map_by_filename(self, folder: Path) -> dict[str, list[str]]:
        mapping: dict[str, list[str]] = {}
        for f in folder.iterdir():
            if f.suffix.lower() not in {".cur", ".ani"}:
                continue
            stem = f.stem.lower()
            mapping[f.name] = _FILENAME_TO_LINUX.get(stem, [stem])
        return mapping

    def _write_index_theme(self, out_theme: Path, name: str) -> None:
        (out_theme / "index.theme").write_text(
            f"[Icon Theme]\nName={name}\n"
            f"Comment={name} (converted from Windows)\n"
            "Inherits=hicolor\n",
            encoding="utf-8",
        )

    def _write_error_log(self, out_theme: Path, exc: Exception) -> None:
        out_theme.mkdir(parents=True, exist_ok=True)
        (out_theme / "conversion-error.txt").write_text(
            f"error={exc}\nPATH={os.environ.get('PATH', '')}\n",
            encoding="utf-8",
        )
