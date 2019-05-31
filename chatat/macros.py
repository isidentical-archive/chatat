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
