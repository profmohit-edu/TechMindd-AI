"""Template pack discovery and selection."""

from __future__ import annotations

import logging
import os
from pathlib import Path


LOGGER = logging.getLogger("techmindd.template_packs")


class TemplatePackRegistry:
    """Discover template packs and resolve configured pack path."""

    def __init__(self, templates_root: str | Path = "templates") -> None:
        self._templates_root = Path(templates_root)
        self._packs = self._discover_packs()
        selected_pack = os.getenv("TEMPLATE_PACK", "default")
        LOGGER.info("Loaded Template Packs: %s", ", ".join(sorted(self._packs)) or "(none)")
        if selected_pack.strip().lower() not in self._packs:
            selected_pack = "default"
        LOGGER.info(
            "Loaded Templates: %s",
            ", ".join(self.template_names(selected_pack)) or "(none)",
        )

    def _discover_packs(self) -> dict[str, Path]:
        packs = {"default": self._templates_root}
        packs_root = self._templates_root / "packs"
        if packs_root.exists():
            for path in sorted(packs_root.iterdir()):
                if path.is_dir():
                    packs[path.name.lower()] = path
        return packs

    def get_pack_path(self, pack_name: str) -> Path:
        key = pack_name.strip().lower()
        if key not in self._packs:
            raise ValueError(f"Unknown template pack: {pack_name}")
        return self._packs[key]

    def template_names(self, pack_name: str) -> list[str]:
        pack_path = self.get_pack_path(pack_name)
        return sorted(path.name for path in pack_path.glob("*.jinja2"))
