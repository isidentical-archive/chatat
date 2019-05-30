import asyncio
import curses
from io import StringIO

from pubmarine import PubPen

from chatat.client import TwitchChatProtocol, TwitchHelixProtocol
from chatat.twitch import Auth, Channel, Message


class ChatInterface:
    def __init__(self, auth, pubpen):
        self.auth = auth
        self.pubpen = pubpen

        self.pubpen.subscribe("message", self.show_message)
        self.pubpen.subscribe("new_char", self.show_typing)

        self._buffer = StringIO()

        self.helix = self.pubpen.loop.run_until_complete(
            TwitchHelixProtocol.session(auth, self.pubpen.loop)
        )

    def __enter__(self):
        self.stdscr = curses.initscr()

        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)

        max_y, max_x = self.stdscr.getmaxyx()

        self.error_buffer = self.stdscr.derwin(1, max_x, 0, 0)

        self.separator1 = self.stdscr.derwin(1, max_x, 1, 0)
        sep_txt = b"-" * (max_x - 1)
        self.separator1.addstr(0, 0, sep_txt)

        self.chat_log = self.stdscr.derwin(max_y - 3, max_x, 2, 0)
        self.chat_max_y, self.chat_max_x = self.chat_log.getmaxyx()
        self.current_chat_line = 0

        self.separator2 = self.stdscr.derwin(1, max_x, max_y - 2, 0)
        sep_txt = b"=" * (max_x - 1)
        self.separator2.addstr(0, 0, sep_txt)

        self.input_buffer = self.stdscr.derwin(1, max_x, max_y - 1, 0)
        self.input_max_y, self.input_max_x = self.input_buffer.getmaxyx()
        self.input_current_x = 0
        self.input_contents = ""

        self.stdscr.refresh()
        return self

    def __exit__(self, *args):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

        return False

    def show_message(self, message):
        if self.current_chat_line >= self.chat_max_y:
            self.pubpen.loop.stop()
            return

        message = f"{message.channel} {message.author}: {message}"

        if len(message) > self.chat_max_x:
            message = message[: self.chat_max_x]

        self.chat_log.addstr(self.current_chat_line, 0, message.encode("utf-8"))
        self.current_chat_line += 1
        self.chat_log.refresh()

    async def get_char(self):
        while True:
            char = chr(await self.pubpen.loop.run_in_executor(None, self.stdscr.getch))
            self.pubpen.publish("new_char", char)

    def show_typing(self, char):
        if char == "\n":
            message = Message.from_simple(
                Channel("btaskaya"), self.auth.username, self._buffer.getvalue()
            )
            self.pubpen.publish("send", message)
            self.pubpen.publish("message", message)
            self.clear_typing()
            return

        self.input_current_x += 1
        self._buffer.write(char)
        self.input_buffer.addstr(0, self.input_current_x - 1, char.encode("utf-8"))
        self.input_buffer.refresh()

    def clear_typing(self):
        self.input_current_x = 0
        self.input_buffer.clear()
        self._buffer.truncate(0)
        self.input_buffer.refresh()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    on_con_lost = loop.create_future()
    auth = Auth.from_json("../twitch_auth.json")
    pubpen = PubPen(loop)

    with ChatInterface(auth, pubpen) as display:
        connection = loop.create_connection(
            lambda: TwitchChatProtocol(
                auth,
                loop,
                channels=[Channel("btaskaya")],
                on_con_lost=on_con_lost,
                pubpen=pubpen,
            ),
            "irc.twitch.tv",
            6667,
        )
        loop.run_until_complete(connection)

        task = loop.create_task(display.get_char())
        loop.run_forever()
        task.cancel()
