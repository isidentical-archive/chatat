import os
import json
import re
from dataclasses import dataclass
from typing import Union
from enum import Enum, auto

PATTERN = re.compile(r"^:(.*?)!(.*?@.*?\.tmi\.twitch\.tv) (.*?) #(.*?) :(.*?)$")


class Actions(Enum):
    PRIVMSG = auto()


@dataclass
class Auth:
    username: str
    password: str
    oauthtok: str

    @classmethod
    def from_json(cls, file: os.PathLike):
        with open(os.fspath(file)) as f:
            content = json.loads(f.read())
        return cls(**content)


@dataclass
class Channel:
    name: str

    def __str__(self):
        return f"#{self.name}"


@dataclass
class Message:
    username: str
    message: str
    host: str

    action: Actions
    channel: Channel

    @classmethod
    def from_raw(cls, raw_msg):
        match = re.match(PATTERN, raw_msg)
        if match:
            return cls(
                match.group(1),
                match.group(5).rstrip(),
                match.group(2),
                getattr(Actions, match.group(3)),
                Channel(match.group(4)),
            )
