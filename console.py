import asyncio

from asyncio import CancelledError
from socket import gethostname, gethostbyname_ex

from peer_exchange import host


use_color = True


async def Autocomplete(text: str, possible: list[str]) -> int:
    """Tries to find a match for given incomplete string from given set of complete options.
        INPUT:
        - text(str) - received input that needs to be completed
        - possible (list[str]) - list of possible matches
        RETURNS:
        - hit (int) - if 1 match was found: index of match, 
            otherwise: {-4: task cancelled; -3: not found, empty string; -2: not found; -1: multiple matches}"""
    try:
        if text == "":
            if "" not in possible:
                return -3 # not found (special handling of "")
            return possible.index(text)
        hit = -2 # not found
        for i in range(len(possible)):
            if possible[i].startswith(text):
                if hit == -2:
                    hit = i
                else:
                    hit = -1 # multiple matches
                    break
        return hit
    except CancelledError:
        return -4


def colorprint(text: str, color: str) -> None:
    """Handles printing in colors (black, red, green, yellow, blue, magenta, cyan, white)
        Does not add line breaks.
        INPUT:
        - text (str) - text to print in color
        - color (str) - desired color's name
        RETURNS NOTHING"""
    colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "reset": "\033[0m"
    }
    if use_color and color in colors:
        print(colors[color], end="")
    print(text, sep="", end="")
    if use_color:
        print(colors["reset"], end="")


async def as_input(prompt: str = "") -> str:
    """Asynchronous input
        INPUT:
        - prompt (str) - prompt to display for user
        RETURNS:
        - user_input (str) - string of user input"""

    loop = asyncio.get_event_loop()
    future = loop.create_future()

    def on_input():
        user_input = input(prompt)
        loop.call_soon_threadsafe(lambda: future.set_result(user_input))
    
    await loop.run_in_executor(None, on_input)
    return await future

# TODO: Maybe let's give this application a name?
async def Console() -> None:
    """Handles console and interactions with user
        INPUT ABSENT
        RETURNS NOTHING"""
    try:
        commands = {
            "help": "List all commands",
            "download": "Download file with name given after a space",
            "list_local": "List locally available files",
            "list_remote": "List downloadable files",
            "set_address": "Select IP address to use by this peer",
            "show_address": "Show IP address currently used by this peer",
            "show_interfaces": "Show IP addresses of all detected interfaces",
            "toggle_color": "Enable/disable colors in terminal"
            }
        cmd_list = list(commands.keys())
        cmd_length = max(len(key) for key in commands.keys())
        print("Welcome to ", end="")
        colorprint("[P2P APP NAME HERE]", "cyan")
        print("!")
        print("Autodetected IP address: ", end="")
        colorprint(f"{host}\n", "cyan")
        print("If the above text appears weird, please use command: toggle_color")
        print("For list of commands, please use command: help")
        while True:
            user_input = (await as_input())
            cmd = user_input.lower().split()
            cmd_id = await Autocomplete(cmd[0], cmd_list)
            cmd_text = ""
            if cmd_id >= 0:
                cmd_text = cmd_list[cmd_id]
            match cmd_text:
                case "help":
                    for key, value in commands.items():
                        colorprint(f"{key:<{cmd_length}} ", "yellow")
                        print(f"- {value}")
                case "toggle_color":
                    global use_color
                    use_color = not use_color
                    print("Set color usage to: ", end="")
                    if use_color:
                        colorprint("On\n", "green")
                    else:
                        print("Off")
                case "show_address":
                    print("Using IP address: ", end="")
                    colorprint(f"{host}\n", "cyan")
                case "show_interfaces":
                    for addr in gethostbyname_ex(gethostname())[2]:
                        colorprint(addr, "cyan")
                        if addr == host:
                            colorprint("\t[BEING USED]", "green")
                        print()


    except CancelledError:
        print("CONSOLE TASK CANCELLED")


if __name__ == "__main__":
    asyncio.run(Console())