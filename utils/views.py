import colorama
import os

from config import config


colorama.init()


class Color:
    def __init__(self, text):
        reset = "\033[0;0m"

        self.red = f"\033[1;31m{text}{reset}"
        self.green = f"\033[1;32m{text}{reset}"
        self.blue = f"\033[1;34m{text}{reset}"
        self.yellow = f"\033[1;33m{text}{reset}"
        self.cyan = f"\033[0;36m{text}{reset}"


def color_status(status):
    status = str(status)

    if status.startswith("2"):
        return Color(status).green
    
    if status.startswith("3"):
        return Color(status).yellow
    
    if status.startswith(("4", "5")):
        return Color(status).red
   
    return status


def limited_print(text, end="\n"):
    size = os.get_terminal_size().columns
  
    if len(text) >= size:
        text = f"{text[:size]}{Color('...').cyan}"

    print(text, end=end)


def print_result(url, status="000", valid=False, message=""):
    print("\033[2K", end="\r")

    if valid:
        limited_print(f"[{Color('+').green}] {color_status(status)} - {url}")

    done = config.request_manager.done
    total = config.request_manager.total

    text = f"[{Color('process').cyan}] {done}/{total} "
    text += f"[{Color('message').cyan}]: {message} "
    text += f"[{Color('url').cyan}] {url}"

    limited_print(text, end="\r")

    if done == total:
        print("\033[2K", end="\r")