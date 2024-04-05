import asyncio
from itertools import cycle
import netifaces

from asyncio import CancelledError
from socket import gethostname, gethostbyname_ex

import globals

from globals import getAddresses
from file_sharing import trackpieces, shdir


use_color = True




async def autocomplete(text: str, possible: list[str]) -> int:
    """Tries to find a match for given incomplete string from given set of complete options.
        INPUT:
        - text (string) - received input that needs to be completed
        - possible (list[string]) - list of possible matches
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
        - text (string) - text to print in color
        - color (string) - desired color's name
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
        - prompt (string) - prompt to display for user
        RETURNS:
        - user_input (string) - string of user input"""

    loop = asyncio.get_event_loop()
    future = loop.create_future()

    def on_input():
        user_input = input(prompt)
        loop.call_soon_threadsafe(lambda: future.set_result(user_input))
    
    await loop.run_in_executor(None, on_input)
    return await future


async def console() -> None:
    """Handles console and interactions with user
        INPUT ABSENT
        RETURNS NOTHING"""
    try:
        commands = {
            "help": "List all commands",
            "exit": "Exits the program",
            "download": "Download file with name given after a space",
            "list_local": "List locally available files",
            "list_remote": "List downloadable files",
            "set_address": "Select IP address to use by this peer",
            "show_address": "Show IP address currently used by this peer",
            "show_interfaces": "Show IP addresses of all detected interfaces",
            "toggle_color": "Enable/disable colors in terminal",
            "update_shared": "Updates files being shared "
            }
        cmd_list = list(commands.keys())
        cmd_length = max(len(key) for key in commands.keys())
        print("Welcome to ", end="")
        colorprint("QT-Share", "cyan")
        print("!")
        print("Autodetected IP address: ", end="")
        colorprint(f"{globals.host}\n", "cyan")
        print("If the above text appears weird, please use command: toggle_color")
        print("For list of commands, please use command: help")
        while globals.run:
            user_input = (await as_input())
            cmd = user_input.lower().split()
            if len(cmd) == 0:
                continue
            cmd_id = await autocomplete(cmd[0], cmd_list)
            cmd_text = ""
            if cmd_id >= 0:
                cmd_text = cmd_list[cmd_id]
            match cmd_text:
                case "help":
                    for key, value in commands.items():
                        colorprint(f"{key:<{cmd_length}} ", "yellow")
                        print(f"- {value}")
                case "exit":
                    globals.run = False
                    raise SystemExit
                case "download":
                    
                    async def download(filename, download_finished) -> bool:
                        """Runs the download
                            INPUT:
                            - filename (string) - item to be downloaded
                            - download_finished (asyncio.Event) - event to set when finished
                            RETURNS:
                            - download_possible (bool) - indictation whether download succeeded"""
                        try:
                            resources:list[str] = []
                            piecenum:int = 1
                            async with globals.peers_lock:
                                for addr in globals.peers.keys():
                                    for l in globals.peers[addr][1:-1]:
                                        for s in l:
                                            if s.find(filename) != -1:
                                                piecenum = int(s.split(":")[-1])
                                                resources.append(f"{addr}:{s}")
                            download_possible = len(resources) >= piecenum
                            if download_possible:
                                download_possible = await trackpieces(filename,resources)
                            download_finished.set()
                            return download_possible
                        except CancelledError:
                            return False

                    async def animation(download_finished) -> None:
                        """Displays downloading animation
                            INPUT:
                            - download_finished (asyncio.Event) - event that will be set when finished
                            RETURNS NOTHING"""
                        try:
                            if use_color:
                                print('\033[?25l', end='') # Hide cursor
                            frames = cycle(r'-\|/-\|/')
                            while not download_finished.is_set():
                                frame = next(frames)
                                print('\rDownloading... ', frame, sep='', end='', flush=True)
                                await asyncio.sleep(0.1)
                                if download_finished.is_set():
                                    break
                                await asyncio.sleep(0.1)
                            print('\rDownloading... ', sep='', end='', flush=True)
                            if use_color:
                                print('\033[?25h', end='') # Show cursor again
                            return
                        except CancelledError:
                            if use_color:
                                print('\033[?25h', end='') # Show cursor again
                            return                        
                    
                    if len(cmd) != 2:
                        colorprint("Usage: download [Filename]\n", "red")
                    else:
                        filename:str = cmd[1]
                        download_finished = asyncio.Event()
                        download_successful, _ = await asyncio.gather(
                            download(filename, download_finished),
                            animation(download_finished)
                        )
                        if download_successful:
                            colorprint("DONE\n", "green")
                            colorprint(f"Finished downloading file {filename}\n", "green")
                        else:
                            colorprint("FAIL\n", "red")
                            colorprint("Unable to obtain requested file\n", "red")
                case "list_local":
                    async with globals.resource_list_lock:
                        res_list = sorted(set(map(lambda pieces_list: pieces_list.split(":")[0], globals.resource_list))) # see case "list_remote"
                    for res in res_list:
                        colorprint(f"{res} \t", "yellow")
                    if len(res_list) == 0:
                        colorprint("No local files are being shared", "red")
                    print()
                case "list_remote":
                    async with globals.resource_list_lock:
                        lists = list(map(lambda x: x[1][1], globals.peers.items()))  # get lists of filepieces from all peers
                    pieces_list: list[str] = list(set().union(*lists)) # merge filepieces lists into one list
                    res_list = sorted(set(map(lambda pieces_list: pieces_list.split(":")[0], pieces_list))) # get just the filename, remove duplicates, sort alphabetically
                    for res in res_list:
                        colorprint(f"{res} \t", "yellow")
                    if len(res_list) == 0:
                        colorprint("No remote files found", "red")
                    print()
                case "set_address":
                    if len(cmd) != 2:
                        colorprint("Usage: set_address [IP address]\n", "red")
                    elif cmd[1] not in getAddresses():
                        colorprint("IP address must be of a valid interface, use show_interfaces to see all available\n", "red")
                    else:
                        globals.host = cmd[1]
                        globals.resetPEX.set()
                        print("Now using address:  ", end="")
                        colorprint(f"{globals.host}\n", "cyan")
                case "show_address":
                    print("Using IP address: ", end="")
                    colorprint(f"{globals.host}\n", "cyan")
                case "show_interfaces":
                    for addr in getAddresses():
                        colorprint(addr, "cyan")
                        if addr == globals.host:
                            colorprint("\t[BEING USED]", "green")
                        print()
                case "toggle_color":
                    global use_color
                    use_color = not use_color
                    print("Set color usage to: ", end="")
                    if use_color:
                        colorprint("On\n", "green")
                    else:
                        print("Off")
                case "update_shared":
                    globals.resetAnnouncementsPEX.set()
                    print("Announcements updated")
                case _:
                    pass
    except CancelledError:
        globals.run = False
        raise SystemExit


if __name__ == "__main__":
    asyncio.run(console())
