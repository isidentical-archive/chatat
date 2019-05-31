from collections import defaultdict
from chatat.twitch import Actions


class Macros:
    macros = defaultdict(list)

    def __init__(self, pubpen):
        self.pubpen = pubpen

    def dispatch(self, message):
        for macro in self.macros[message.action]:
            macro(self.pubpen, message)

    @classmethod
    def macro(cls, on_event):
        def wrapper(func):
            cls.macros[on_event].append(func)
            return func

        return wrapper


@Macros.macro(Actions.PRIVMSG)
def on_gnu(publisher, message):
    lower_message = message.message.lower()
    author = message.author
    if "linux" in lower_message and "gnu" not in lower_message:
        publisher.publish("outgoing", f"{author} dude; not linux, GNU/Linux")
