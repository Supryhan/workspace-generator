import os
from pathlib import Path


def resolve_path(path_str: str | Path) -> Path:
    """
    Expands ~ to home directory and returns an absolute resolved path.
    """
    return Path(path_str).expanduser().resolve()


def safe_mkdir(path: Path, dry_run: bool = False) -> None:
    """
    Safely creates a directory (and all parents) unless dry_run is True.
    """
    if dry_run:
        print(f"[DRY-RUN] Create directory: {path}")
        return
    path.mkdir(parents=True, exist_ok=True)


def safe_write(path: Path, content: str, dry_run: bool = False, force: bool = False) -> bool:
    """
    Writes content to path, respecting overwrite guards.
    Returns True if written, False if skipped due to existing file.
    """
    if path.exists() and not force:
        if dry_run:
            print(f"[DRY-RUN] File already exists, skip writing: {path}")
        return False

    if dry_run:
        print(f"[DRY-RUN] Write file ({len(content)} bytes): {path}")
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def make_executable(path: Path, dry_run: bool = False) -> None:
    """
    Marks a file as executable (chmod +x equivalent).
    """
    if dry_run:
        print(f"[DRY-RUN] Mark executable: {path}")
        return
    if path.exists():
        path.chmod(path.stat().st_mode | 0o111)
