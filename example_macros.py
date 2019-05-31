from chatat.macros import Macros
from chatat.twitch import Actions


@Macros.macro(Actions.PRIVMSG)
def on_gnu(publisher, message):
    lower_message = message.message.lower()
    author = message.author
    if "linux" in lower_message and "gnu" not in lower_message:
        publisher.publish("outgoing", f"{author} dude; not linux, GNU/Linux")
