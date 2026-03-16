"""Custom hatch build hook to bundle frontend SPA assets."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Copy frontend SPA build into the package if available."""

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Copy frontend dist-spa into qkd_playground/static/."""
        root = Path(self.root)
        frontend_dist = (root / ".." / "frontend" / "dist-spa").resolve()
        static_dest = root / "src" / "qkd_playground" / "static"

        if not frontend_dist.is_dir():
            # Frontend not built — skip (dev/editable mode)
            return

        # Clean and copy into the package source tree
        if static_dest.exists():
            shutil.rmtree(static_dest)
        shutil.copytree(frontend_dist, static_dest)
