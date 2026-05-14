from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from endstone import Logger


class MessagesLoader:

    def __init__(self, data_folder: Path, logger: Logger) -> None:
        self._data_folder = data_folder
        self._logger = logger

    def load(self, defaults: dict[str, str]) -> dict[str, str]:
        self._data_folder.mkdir(parents=True, exist_ok=True)
        filepath = self._data_folder / "messages.yml"
        if not filepath.exists():
            self._save_yaml(filepath, defaults)
            return dict(defaults)
        try:
            with filepath.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                self._logger.warning("Invalid messages.yml, using defaults.")
                return dict(defaults)
            return self._deep_merge(defaults, data)
        except Exception as e:
            self._logger.error(f"Error loading messages.yml: {e}")
            return dict(defaults)

    def _save_yaml(self, filepath: Path, data: dict) -> None:
        try:
            with filepath.open("w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        except Exception as e:
            self._logger.error(f"Error saving messages.yml: {e}")

    @staticmethod
    def _deep_merge(defaults: dict, overrides: dict) -> dict:
        result = dict(defaults)
        for key, value in overrides.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = MessagesLoader._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
