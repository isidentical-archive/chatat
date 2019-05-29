import asyncio
from typing import Sequence
from chatat.twitch import Auth, Channel, Message


class TwitchChatProtocol(asyncio.Protocol):
    def __init__(self, auth: Auth, channels: Sequence[Channel], on_con_lost, loop):
        self.on_con_lost = on_con_lost
        self._auth = auth
        self._channels = channels

    def _send(self, cmd, value):
        request = f"{cmd.upper()} {value}\r\n"
        self.transport.write(request.encode("utf-8"))

    def connection_made(self, transport):
        self.transport = transport

        self._send("pass", self._auth.oauthtok)
        self._send("nick", self._auth.username)
        for channel in self._channels:
            self._send("join", channel)

    def data_received(self, data):
        msg = Message.from_raw(data.decode())
        if msg:
            print(msg)

    def connection_lost(self, exc):
        print("The server closed the connection")
        self.on_con_lost.set_result(True)
