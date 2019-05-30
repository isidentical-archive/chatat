from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Optional, Tuple, Union

PATTERN = re.compile(r"^:(.*?)!(.*?@.*?\.tmi\.twitch\.tv) (.*?) #(.*?) :(.*?)$")


class Actions(Enum):
    PRIVMSG = auto()


@dataclass
class Auth:
    username: str
    oauthtok: str

    client_id: str
    client_secret: str

    @classmethod
    def from_json(cls, file: os.PathLike):
        with open(os.fspath(file)) as f:
            content = json.loads(f.read())
        return cls(**content["chat"], **content["helix"])  # type: ignore


class SingleableChannel:
    def __init_subclass__(cls: SingleableChannel) -> None:
        cls._singletons: Dict[Tuple[Any, ...], SingleableChannel] = {}

    def __new__(cls: SingleableChannel, *args) -> SingleableChannel:
        if not cls._singletons.get(args):
            cls._singletons[args] = super().__new__(cls)
        return cls._singletons[args]


@dataclass
class Channel(SingleableChannel):
    name: str

    def __str__(self):
        return f"#{self.name}"


@dataclass
class Message:
    author: str
    message: str
    host: str

    action: Actions
    channel: Channel

    @classmethod
    def from_simple(cls, channel: Channel, author: str, message: str):
        return cls(author, message, None, None, channel)

    @classmethod
    def from_raw(cls, raw_msg: str) -> Optional[Message]:
        match = re.match(PATTERN, raw_msg)
        if match:
            return cls(
                match.group(1),
                match.group(5).rstrip(),
                match.group(2),
                getattr(Actions, match.group(3)),
                Channel(match.group(4)),
            )
        return None

    def __str__(self):
        return self.message
