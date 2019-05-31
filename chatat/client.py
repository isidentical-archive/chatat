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
        self.pubpen = kwargs.pop("pubpen", None)

        self.loop = loop
        self._auth = auth

        self.logger = logging.getLogger(__name__)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.ERROR)

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
            cookie_jar=jar,
            headers={
                "Client-ID": inst._auth.client_id,
                "Authorization": f"Bearer {inst._auth.client_secret}",
            },
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pubpen.subscribe("send", self._send_to_channel)
        self.pubpen.subscribe("switch_channel", self._switch_channel)

        self._active_channels = []

    def _send_irc_command(self, cmd: str, value: str) -> None:
        request = f"{cmd.upper()} {value}\r\n"
        self.transport.write(request.encode("utf-8"))

    def _send_to_channel(self, message: Message) -> None:
        self._send_irc_command("privmsg", f"{message.channel} :{message.message}")

    def _switch_channel(self, channel: Channel) -> None:
        if not channel in self._active_channels:
            self._send_irc_command("join", channel)
            self._active_channels.append(channel)

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
            self._active_channels.append(channel)

    def data_received(self, raw_msg: bytes) -> None:
        data = raw_msg.decode()
        msg = Message.from_raw(data)
        self.logger.info(msg or data)
        if msg:
            self.pubpen.publish("message", msg)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.logger.info("The server closed the connection")
        self.on_con_lost.set_result(True)
