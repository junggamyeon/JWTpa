from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from endstone import Logger


_DEFAULT_CONFIG = {
    "tpa": {
        "timeout-seconds": 60,
        "cooldown-seconds": 0,
    },
    "debug": False,
}


class ConfigLoader:

    def __init__(self, data_folder: Path, logger: Logger) -> None:
        self._data_folder = data_folder
        self._logger = logger
        self._config: dict[str, Any] = {}

    @property
    def tpa_config(self) -> dict[str, Any]:
        return self._config.get("tpa", _DEFAULT_CONFIG["tpa"])

    @property
    def debug(self) -> bool:
        return self._config.get("debug", False)

    def load(self) -> None:
        self._data_folder.mkdir(parents=True, exist_ok=True)
        self._config = self._load_yaml("config.yml", _DEFAULT_CONFIG)

    def reload(self) -> None:
        self.load()

    def _load_yaml(self, filename: str, defaults: dict) -> dict:
        filepath = self._data_folder / filename

        if not filepath.exists():
            self._save_yaml(filepath, defaults)
            return dict(defaults)

        try:
            with filepath.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                self._logger.warning(f"Invalid {filename}, using defaults.")
                return dict(defaults)

            return self._deep_merge(defaults, data)

        except Exception as e:
            self._logger.error(f"Error loading {filename}: {e}")
            return dict(defaults)

    def _save_yaml(self, filepath: Path, data: dict) -> None:
        try:
            with filepath.open("w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
        except Exception as e:
            self._logger.error(f"Error saving {filepath.name}: {e}")

    @staticmethod
    def _deep_merge(defaults: dict, overrides: dict) -> dict:
        result = dict(defaults)

        for key, value in overrides.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = ConfigLoader._deep_merge(result[key], value)
            else:
                result[key] = value

        return result