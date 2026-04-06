from __future__ import annotations

import os
from pathlib import Path

from .errors import SymlinkConflictError


def ensure_symlink(*, link_path: Path, target_path: Path, dry_run: bool) -> str:
    rendered = f"ln -s {target_path} {link_path}"
    if dry_run:
        return rendered

    if link_path.is_symlink():
        link_path.unlink()
    elif link_path.exists():
        raise SymlinkConflictError(
            f"cannot create symlink at '{link_path}': path already exists and is not a symlink"
        )
    elif os.path.lexists(link_path):
        link_path.unlink()

    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.symlink_to(target_path)
    return rendered
