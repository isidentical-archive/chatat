from collections import defaultdict
from chatat.twitch import Actions


class Macros:
    macros = defaultdict(list)

    def __init__(self, pubpen, helix, loop):
        self.publisher = pubpen
        self.helix = helix
        self.loop = loop

    def dispatch(self, message):
        for macro in self.macros[message.action]:
            macro(self, message)

    @classmethod
    def macro(cls, on_event):
        def wrapper(func):
            cls.macros[on_event].append(func)
            return func

        return wrapper
