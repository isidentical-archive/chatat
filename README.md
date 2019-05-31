# Chatat
## Features
- Nice, cursed terminal ui.
- Completly asynchronous
- Connecting to multiple channels and listening them
- Switching between channels
- Quitting channels
- Twitch Helix API
- **MACROS**

## Macros
You can register macros to certain events. For an example when a message posted to channel you can reply it like you are a bot. Create a python module in starting directory. The name doesn't matter. `example_module.py`

Import `Macros` for registering your macro and `Actions` for choosing event to register.
```py
from chatat.macros import Macros
from chatat.twitch import Actions
```
And then register with `Macros.macro`
```py
@Macros.macro(Actions.PRIVMSG)
def macro(*blabla):
    ...
```
The macro takes `handler` (for accessing services) and `message` (a `chatat.twitch.Message` object that holds message / author etc.)
```py
def on_gnu(handler, message):
    lower_message = message.message.lower()
    author = message.author
    if "linux" in lower_message and "gnu" not in lower_message:
        ...
```
Send with `handler.publisher`
```py
        handler.publisher.publish("outgoing", f"{author} dude; not linux, GNU/Linux")
```
### Helix API
Current version supports usage of Twitch Helix API with a little wrapper.
```
await handler.helix.get(endpoint, **params) -> JSON Response
await handler.helix.get("streams", game_id=33214) -> {...}
```
