import asyncio
from chatat.client import TwitchChatProtocol
from chatat.twitch import Auth, Channel


async def main():
    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()

    auth = Auth.from_json("../twitch_auth.json")
    transport, protocol = await loop.create_connection(
        lambda: TwitchChatProtocol(auth, [Channel("btaskaya")], on_con_lost),
        "irc.twitch.tv",
        6667,
    )

    try:
        await on_con_lost
    finally:
        transport.close()


asyncio.run(main())
