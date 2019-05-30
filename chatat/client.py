import asyncio
import logging
import sys
from contextlib import suppress
from typing import Sequence, Optional
from chatat.twitch import Auth, Channel, Message


class TwitchChatProtocol(asyncio.Protocol):
    def __init__(self, auth: Auth, channels: Sequence[Channel], on_con_lost: asyncio.Future) -> None:
        self.on_con_lost = on_con_lost
        self._auth = auth
        self._channels = channels

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)


    def _send(self, cmd: str, value: str) -> None:
        request = f"{cmd.upper()} {value}\r\n"
        self.transport.write(request.encode("utf-8"))

    def connection_made(self, transport: asyncio.transports.Transport):
        self.transport = transport

        self._send("pass", self._auth.oauthtok)
        self._send("nick", self._auth.username)
        with suppress(ValueError):
            ip, port = transport.get_extra_info('peername')
            self.logger.info(f"Connection made to {ip}:{port}")
        for channel in self._channels:
            self._send("join", channel)

    def data_received(self, data: bytes) -> None:
        msg = Message.from_raw(data.decode())
        if msg:
            self.logger.info(msg)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.logger.info("The server closed the connection")
        self.on_con_lost.set_result(True)
