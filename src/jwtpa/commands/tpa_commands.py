from __future__ import annotations

from typing import TYPE_CHECKING

from endstone import Player
from endstone.command import CommandSender
from endstone.level import Location

if TYPE_CHECKING:
    from jwtpa.main import JWTpa


class TPACommandHandler:

    def __init__(self, plugin: JWTpa) -> None:
        self._plugin = plugin

    def handle(self, sender: CommandSender, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_message(self._plugin.msg("player-only"))
            return True

        if not args:
            sender.send_message(self._plugin.msg("tpa-usage"))
            return True

        target_name = args[0]
        target = self._plugin.server.get_player(target_name)
        if target is None:
            sender.send_message(self._plugin.msg("player-not-found", player=target_name))
            return True

        if target.name.lower() == sender.name.lower():
            sender.send_message(self._plugin.msg("self-teleport"))
            return True

        sender_uuid = str(sender.unique_id)
        receiver_uuid = str(target.unique_id)
        target_display = target.name
        sender_display = sender.name

        async def task():
            try:
                has_active = await self._plugin._tpa_repo.has_active_request(sender_uuid, receiver_uuid)
                if has_active:
                    def notify():
                        sender.send_message(self._plugin.msg("tpa-already-sent", player=target_display))
                    self._plugin.server.scheduler.run_task(self._plugin, notify)
                    return

                await self._plugin._tpa_repo.create_request(
                    sender_uuid=sender_uuid,
                    sender_name=sender_display,
                    receiver_uuid=receiver_uuid,
                    receiver_name=target_display,
                )

                def notify_sender():
                    sender.send_message(self._plugin.msg("tpa-sent", player=target_display))

                def notify_target():
                    target.send_message(self._plugin.msg("tpa-received", player=sender_display))
                    target.send_message(self._plugin.msg("tpa-type-accept"))
                    target.send_message(self._plugin.msg("tpa-timeout-info", seconds=60))

                self._plugin.server.scheduler.run_task(self._plugin, notify_sender)
                self._plugin.server.scheduler.run_task(self._plugin, notify_target)
            except Exception as e:
                self._plugin.logger.error(f"TPA request error: {e}")

        self._plugin.run_async(task())
        return True

class TPAHereCommandHandler:

    def __init__(self, plugin: JWTpa) -> None:
        self._plugin = plugin

    def handle(self, sender: CommandSender, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_message(self._plugin.msg("player-only"))
            return True

        if not args:
            sender.send_message(self._plugin.msg("tpahere-usage"))
            return True

        target = self._plugin.server.get_player(args[0])
        if target is None:
            sender.send_message(self._plugin.msg("player-not-found", player=args[0]))
            return True

        if target.name.lower() == sender.name.lower():
            sender.send_message(self._plugin.msg("self-teleport"))
            return True

        sender_uuid = str(sender.unique_id)
        receiver_uuid = str(target.unique_id)

        loc = sender.location

        async def task():
            try:
                await self._plugin._tpa_repo.create_request(
                    sender_uuid=sender_uuid,
                    sender_name=sender.name,
                    receiver_uuid=receiver_uuid,
                    receiver_name=target.name,
                    world=loc.dimension.name,
                    x=loc.x,
                    y=loc.y,
                    z=loc.z,
                    yaw=loc.yaw,
                    pitch=loc.pitch,
                )

                def notify():
                    sender.send_message(self._plugin.msg("tpa-sent", player=target.name))
                    target.send_message(self._plugin.msg("tpahere-received", player=sender.name))
                    target.send_message(self._plugin.msg("tpa-type-accept"))
                    target.send_message(self._plugin.msg("tpa-timeout-info", seconds=60))

                self._plugin.server.scheduler.run_task(self._plugin, notify)

            except Exception as e:
                self._plugin.logger.error(f"TPAHere request error: {e}")

        self._plugin.run_async(task())
        return True
class TPAcceptCommandHandler:

    def __init__(self, plugin: JWTpa) -> None:
        self._plugin = plugin

    def handle(self, sender: CommandSender, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_message(self._plugin.msg("player-only"))
            return True

        async def task():
            try:
                receiver_uuid = str(sender.unique_id)
                request = await self._plugin._tpa_repo.get_active_request_for_receiver(receiver_uuid)

                if request is None:
                    def notify():
                        sender.send_message(self._plugin.msg("tpa-no-request"))
                    self._plugin.server.scheduler.run_task(self._plugin, notify)
                    return

                sender_player = self._plugin.server.get_player(request.sender_name)
                if sender_player is None:
                    await self._plugin._tpa_repo.delete_request(request.id)
                    def notify_offline():
                        sender.send_message(self._plugin.msg("tpa-requester-offline"))
                    self._plugin.server.scheduler.run_task(self._plugin, notify_offline)
                    return

                await self._plugin._tpa_repo.delete_request(request.id)

                def do_teleport():
                    sender.send_message(self._plugin.msg("tpa-accepted"))
                    if sender_player:
                        sender_player.send_message(self._plugin.msg("tpa-accepted"))

                    if request.world:
                        # tpahere: acceptor teleports to saved location
                        dim = self._plugin.server.level.get_dimension(request.world)
                        if dim:
                            loc = Location(
                                dim,
                                request.x,
                                request.y,
                                request.z,
                                request.pitch or 0,
                                request.yaw or 0,
                            )
                            sender.teleport(loc)
                            return

                    # tpa: original requester teleports to acceptor
                    sender_player.teleport(sender.location)

                self._plugin.server.scheduler.run_task(self._plugin, do_teleport)

            except Exception as e:
                self._plugin.logger.error(f"TPAccept error: {e}")

        self._plugin.run_async(task())
        return True
class TPAcceptHandler:

    def __init__(self, plugin: JWTpa) -> None:
        self._plugin = plugin

    def handle(self, sender: CommandSender, args: list[str]) -> bool:
        return TPAcceptCommandHandler(self._plugin).handle(sender, args)


class TPAcDenyHandler:

    def __init__(self, plugin: JWTpa) -> None:
        self._plugin = plugin

    def handle(self, sender: CommandSender, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_message(self._plugin.msg("player-only"))
            return True

        async def task():
            try:
                receiver_uuid = str(sender.unique_id)
                request = await self._plugin._tpa_repo.get_active_request_for_receiver(receiver_uuid)
                if request is None:
                    def notify():
                        sender.send_message(self._plugin.msg("tpa-no-request"))
                    self._plugin.server.scheduler.run_task(self._plugin, notify)
                    return

                await self._plugin._tpa_repo.delete_request(request.id)

                def notify():
                    sender.send_message(self._plugin.msg("tpa-declined"))
                self._plugin.server.scheduler.run_task(self._plugin, notify)
            except Exception as e:
                self._plugin.logger.error(f"TPADeny error: {e}")

        self._plugin.run_async(task())
        return True


class TPAcCancelHandler:

    def __init__(self, plugin: JWTpa) -> None:
        self._plugin = plugin

    def handle(self, sender: CommandSender, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_message(self._plugin.msg("player-only"))
            return True

        async def task():
            try:
                sender_uuid = str(sender.unique_id)
                request = await self._plugin._tpa_repo.get_active_request_by_sender(sender_uuid)
                if request is None:
                    def notify():
                        sender.send_message(self._plugin.msg("tpa-no-request"))
                    self._plugin.server.scheduler.run_task(self._plugin, notify)
                    return

                await self._plugin._tpa_repo.delete_request(request.id)

                def notify():
                    sender.send_message(self._plugin.msg("tpa-cancelled"))
                self._plugin.server.scheduler.run_task(self._plugin, notify)
            except Exception as e:
                self._plugin.logger.error(f"TPAcancel error: {e}")

        self._plugin.run_async(task())
        return True


