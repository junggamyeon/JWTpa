from __future__ import annotations

from typing import Any


_DEFAULT_MESSAGES = {
    "prefix": "&6&l[JWTpa]&r ",
    "error-generic": "{prefix}&cAn internal error occurred. Please try again.",
    "player-only": "{prefix}&cThis command can only be used by players.",
    "no-permission": "{prefix}&cYou do not have permission to do that.",
    "self-teleport": "{prefix}&cYou cannot teleport to yourself.",
    "player-not-found": "{prefix}&cPlayer '{player}' not found.",
    "tpa-usage": "&c/tpa <player>",
    "tpahere-usage": "&c/tpahere <player>",
    "tpa-sent": "{prefix}&aYou sent a teleport request to {player}.",
    "tpa-received": "{prefix}&a{player} would like to teleport to you.",
    "tpahere-received": "{prefix}&a{player} would like you to teleport to them.",
    "tpa-type-accept": "&eType &a/tpaccept&e to accept, &c/tpdeny&e to deny.",
    "tpa-timeout-info": "&7Request expires in {seconds} seconds.",
    "tpa-already-sent": "{prefix}&cYou already have a pending request to {player}.",
    "tpa-no-request": "{prefix}&cNo pending teleport request.",
    "tpa-accepted": "{prefix}&aTeleport request accepted!",
    "tpa-accepted-auto": "{prefix}&aTeleport request auto-accepted (teleport enabled).",
    "tpa-declined": "{prefix}&cTeleport request declined.",
    "tpa-cancelled": "{prefix}&cTeleport request cancelled.",
    "tpa-expired": "{prefix}&cYour teleport request expired.",
    "tpa-requester-offline": "{prefix}&cThe requester is no longer online.",
}


class MessageFormatter:

    def __init__(self, prefix: str = "[JWTpa]", messages: dict[str, str] | None = None) -> None:
        self._messages = messages or dict(_DEFAULT_MESSAGES)
        self._prefix = self._get_raw("prefix", "&6&l[JWTpa]&r ")

    def _get_raw(self, key: str, fallback: str = "") -> str:
        return self._messages.get(key, fallback)

    def format(self, key: str, **kwargs: Any) -> str:
        raw = self._messages.get(key)
        if raw is None:
            return f"§cMissing message: {key}"
        template = raw
        kwargs.setdefault("prefix", self._prefix)
        try:
            result = template.format(**kwargs)
        except (KeyError, ValueError):
            return template
        return self._translate_colors(result)

    def _translate_colors(self, text: str) -> str:
        return text.replace("&", "§")

    def reload(self, messages: dict[str, str]) -> None:
        self._messages = messages
        self._prefix = self._get_raw("prefix", "&6&l[JWTpa]&r ")

    @property
    def prefix(self) -> str:
        return self._translate_colors(self._prefix)
