from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from endstone.plugin import Plugin

from jwtpa.database.database_manager import DatabaseManager
from jwtpa.database.schema import SchemaManager
from jwtpa.database.repositories.tpa_repository import TPARequestRepository
from jwtpa.commands.tpa_commands import (
    TPACommandHandler,
    TPAHereCommandHandler,
    TPAcceptHandler,
    TPAcDenyHandler,
    TPAcCancelHandler,
)
from jwtpa.util.config_loader import ConfigLoader
from jwtpa.util.messages_loader import MessagesLoader
from jwtpa.util.message_formatter import MessageFormatter

if TYPE_CHECKING:
    from concurrent.futures import Future

class JWTpa(Plugin):
    api_version = "0.11"
    prefix = "[JWTpa]"
    version = "1.0.0"
    description = "JWTpa - Teleport request plugin for EndstoneMC."
    authors = ["JWDev"]

    commands = {
        "tpa": {
            "description": "Request teleport to a player",
            "usages": ["/tpa <player: string>"],
        },
        "tpahere": {
            "description": "Request player to teleport to you",
            "usages": ["/tpahere <player: string>"],
        },
        "tpaccept": {
            "description": "Accept teleport request",
            "usages": ["/tpaccept"],
            "aliases": ["tpaaccept", "tpac"],
        },
        "tpdeny": {
            "description": "Decline teleport request",
            "usages": ["/tpdeny"],
            "aliases": ["tpadeny", "tpad"],
        },
        "tpcancel": {
            "description": "Cancel your teleport request",
            "usages": ["/tpcancel"],
        },
    }

    permissions = {
        "jwtpa.*": {
            "description": "All JWTpa permissions",
            "default": "op",
            "children": {
                "jwtpa.tpa": True,
                "jwtpa.tpahere": True,
                "jwtpa.tpaccept": True,
                "jwtpa.tpdeny": True,
                "jwtpa.tpcancel": True,
            },
        },
        "jwtpa.tpa": {"description": "Use /tpa command", "default": "true"},
        "jwtpa.tpahere": {"description": "Use /tpahere command", "default": "true"},
        "jwtpa.tpaccept": {"description": "Use /tpaccept command", "default": "true"},
        "jwtpa.tpdeny": {"description": "Use /tpdeny command", "default": "true"},
        "jwtpa.tpcancel": {"description": "Use /tpcancel command", "default": "true"},
    }

    def __init__(self):
        super().__init__()
        self._loop = asyncio.new_event_loop()
        self._loop_thread = None
        self._db_manager: DatabaseManager | None = None
        self._schema_manager: SchemaManager | None = None
        self._tpa_repo: TPARequestRepository | None = None
        self._messages: dict[str, str] = {}
        self._message_formatter = MessageFormatter()

    def on_load(self) -> None:
        import threading

        def start_loop(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()

        self._loop_thread = threading.Thread(target=start_loop, args=(self._loop,), daemon=True)
        self._loop_thread.start()



    def on_enable(self) -> None:
        data_folder = Path(self.data_folder)
        data_folder.mkdir(parents=True, exist_ok=True)

        self._config_loader = ConfigLoader(data_folder, self.logger)
        self._config_loader.load()

        msg_loader = MessagesLoader(data_folder, self.logger)

        resource_path = Path(__file__).parent / "resources" / "messages.yml"
        defaults = {}

        if resource_path.exists():
            import yaml
            with resource_path.open("r", encoding="utf-8") as f:
                defaults = yaml.safe_load(f) or {}

        self._messages = msg_loader.load(defaults)
        self._message_formatter = MessageFormatter(self.prefix, self._messages)

        db_path = str(data_folder / "tpa.db")
        self._db_manager = DatabaseManager(db_path, self.logger)
        self._schema_manager = SchemaManager(self._db_manager, self.logger)
        self._tpa_repo = TPARequestRepository(self._db_manager)

        future = self.run_async(self._init_database())
        try:
            future.result(timeout=10.0)
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            self.server.plugin_manager.disable_plugin(self)
            return

        self._register_commands()
        self.server.scheduler.run_task(
            self,
            self._expire_tpa_requests_task,
            delay=600,
            period=600,
        )
    def on_disable(self) -> None:
        future = self.run_async(self._db_manager.close())
        try:
            future.result(timeout=5.0)
        except Exception as e:
            self.logger.error(f"Error closing database: {e}")

    async def _init_database(self) -> None:
        await self._db_manager.connect()
        await self._schema_manager.create_tables()

    def run_async(self, coro) -> Future[Any]:
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def _register_commands(self) -> None:
        self._tpa_handler = TPACommandHandler(self)
        self._tpahere_handler = TPAHereCommandHandler(self)
        self._tpaccept_handler = TPAcceptHandler(self)
        self._tpadeny_handler = TPAcDenyHandler(self)
        self._tpcancel_handler = TPAcCancelHandler(self)

    def on_command(self, sender, command, args) -> bool:
        cmd_name = command.name.lower()
        if cmd_name == "tpa":
            return self._tpa_handler.handle(sender, args)
        elif cmd_name == "tpahere":
            return self._tpahere_handler.handle(sender, args)
        elif cmd_name == "tpaccept":
            return self._tpaccept_handler.handle(sender, args)
        elif cmd_name == "tpdeny":
            return self._tpadeny_handler.handle(sender, args)
        elif cmd_name == "tpcancel":
            return self._tpcancel_handler.handle(sender, args)
        return False

    def _expire_tpa_requests_task(self) -> None:
        self.run_async(self._tpa_repo.delete_expired_requests())

    def msg(self, key: str, **kwargs) -> str:
        return self._message_formatter.format(key, **kwargs)
