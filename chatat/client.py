import asyncio
import logging
import sys
from contextlib import suppress
from typing import Optional, Sequence

import aiohttp

from chatat.twitch import Auth, Channel, Message


class _Protocol:
    def __init__(self, auth: Auth, loop: asyncio.BaseEventLoop, **kwargs) -> None:

        self.on_con_lost = kwargs.pop("on_con_lost", None)
        self.channels = kwargs.pop("channels", None)

        self.loop = loop
        self._auth = auth

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)


class TwitchHelixProtocol(_Protocol):
    BASE = "https://api.twitch.tv/helix/{}"

    @classmethod
    async def session(cls, *args, **kwargs):
        inst = cls(*args, **kwargs)

        jar = aiohttp.CookieJar(unsafe=True)
        inst.session = aiohttp.ClientSession(
            cookie_jar=jar, headers={"Client-ID": inst._auth.client_id}
        )
        return inst

    async def get(self, endpoint: str, **kwargs):
        self.logger.debug(f"Getting {endpoint} with {kwargs}")
        async with self.session.get(
            self.BASE.format(endpoint), params=kwargs
        ) as result:
            content = await result.json()
        return content


class TwitchChatProtocol(_Protocol, asyncio.Protocol):
    def _send_irc_command(self, cmd: str, value: str) -> None:
        request = f"{cmd.upper()} {value}\r\n"
        self.transport.write(request.encode("utf-8"))

    def connection_made(
        self, transport: asyncio.transports.Transport
    ) -> None:  # type: ignore
        self.transport = transport

        self._send_irc_command("pass", self._auth.oauthtok)
        self._send_irc_command("nick", self._auth.username)
        with suppress(ValueError):
            ip, port = transport.get_extra_info("peername")
            self.logger.info(f"Connection made to {ip}:{port}")
        for channel in self.channels:
            self._send_irc_command("join", channel)

    def data_received(self, raw_msg: bytes) -> None:
        data = raw_msg.decode()
        msg = Message.from_raw(data) or data
        self.logger.info(msg)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.logger.info("The server closed the connection")
        self.on_con_lost.set_result(True)
