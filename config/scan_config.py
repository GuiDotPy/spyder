import sys
import os
from random import choice
import argparse
from urllib.parse import urlparse
from inspect import getmembers, isfunction
from pathlib import Path

import httpx
from motor.motor_asyncio import AsyncIOMotorClient

from utils import response_handler
from utils.utils import split_host, set_schema


class RequestManager:
    r = 0
    done = 0
    total = 0
    error_count_per_domain = {}

    rate_limit_status = {# add more
        "429": 0,
        # "403": 0
    }

    def reset(self):
        for status in self.rate_limit_status:
            self.rate_limit_status[status] = 0


class ScanStaticConfig:
    env = os.environ
    base_dir = Path(__file__).resolve().parent.parent
    request_manager = RequestManager()
    mongo_database = AsyncIOMotorClient(serverSelectionTimeoutMS=5000).scan

    file_extensions = (
        ".png", ".jpg", ".webp", ".svg",
        ".gif", ".mp4", ".eot", ".woff2",
        ".woff", ".otf", ".css", ".scss",
        ".ttf", ".jpeg", ".pdf", ".webmanifest"
    )

    with open("wordlists/user-agent.txt", "r") as file:
        user_agent = file.read().splitlines()


class ScanConfig(argparse.Namespace, ScanStaticConfig):
    
    def __init__(self, parser, **kwargs):
        self.parser = parser
        super().__init__(**kwargs)
        self.response_handlers = self._get_response_handlers()

        if self.use_proxy and not self._check_proxy(self.proxies):
            raise self.parser.error("invalid proxy/port")

    @property
    def stdin(self):
        return self._stdin

    @stdin.setter
    def stdin(self, stdin):
        self._stdin = []

        if isinstance(stdin, str):
            raise self.parser.error(f"unrecognized command {stdin}")

        if not stdin.isatty():
            self._stdin = [
                set_schema(url.strip().strip("/"))
                for url in stdin.read().splitlines()
            ]

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, headers):
        parsed_headers = {"user-agent": choice(self.user_agent)}

        for header in headers:
            if not ":" in header:
                raise self.parser.error(
                    "the correct format for headers is "
                    "key:value separated by a space "
                    "ex: cookie:bla authorization:bla"
                )
            
            key, value = header.split(":")
            parsed_headers[key.strip()] = value.strip()
        
        self._headers = parsed_headers

    @property
    def scope_domains(self):
        if not hasattr(self, "_scope_domains"):
            self._scope_domains = set(split_host(url) for url in self.stdin)

        return self._scope_domains

    @property
    def proxies(self):

        if not self.use_proxy:
            return None

        url = urlparse(self.env.get("PROXY_HOST", ""))
        port = self.env.get("PROXY_PORT")
        user = self.env.get("PROXY_USERNAME")
        password = self.env.get("PROXY_PASSWORD")

        if url and url.scheme and url.hostname and port:
            auth = ""

            if user and password:
                auth = f"{user}:{password}@"
            
            proxy = f"{url.scheme}://{auth}{url.hostname}:{port}"

            return {
                "http://": proxy,
                "https://": proxy
            }

        raise self.parser.error("invalid proxy/port")

    def _get_response_handlers(self):
        return [
            func
            for _, func in getmembers(response_handler, isfunction)
            if func.__module__ == "utils.response_handler"
        ]

    def _check_proxy(self, proxy):#
        try:
            httpx.get("https://lumtest.com/myip.json", proxies=proxy)
            return True
        except httpx.RequestError:
            return False


def positive_int(value):
    try:
        if int(value) > 0:
            return int(value)
    except ValueError:
        pass

    raise argparse.ArgumentTypeError(
        "the value must be an int greater than 0"
    )


def get_scan_parser():
    parser = argparse.ArgumentParser(
        usage="python spyder.py [command] [flags]",
        description="for more information, please visit https://github.com/GuiDotPy/spyder"
    )
    parser.add_argument("scan")
    parser.add_argument(
        "stdin",
        nargs="?",
        default=sys.stdin
    )
    parser.add_argument(
        "-c",
        "--max-concurrency",
        type=positive_int,
        default=50,
        help="maximum concurrent requests",
    )
    parser.add_argument(
        "-mt",
        "--max-timeout",
        type=positive_int,
        default=1,
        help="maximum number of retests that can be taken when there is a timeout",
    )
    parser.add_argument(
        "-mrc",
        "--max-recrawl",
        type=positive_int,
        default=2,
        help="maximum recrawl",
    )
    parser.add_argument(
        "-ss",
        "--skip-status",
        type=int,
        default=[],
        nargs="+",
        help="skip responses with this status"
    )
    parser.add_argument(# add regex too
        "-st",
        "--skip-text",
        type=str,
        default=[],
        nargs="+",
        help="skip responses with this text in body"
    )
    parser.add_argument(# add regex too
        "-su",
        "--skip-urls",
        type=str,
        default=[],
        nargs="+",
        help="skip responses with this text in url"
    )
    parser.add_argument(
        "-H",
        "--headers",
        type=str,
        nargs="+",
        default=[],
        help="set custom headers"
    )
    parser.add_argument(
        "-r",
        "--scope-regex",
        type=str,
        help="use a regex to set additional in-scope domains"
    )
    parser.add_argument(
        "-p",
        "--use_proxy",
        action=argparse.BooleanOptionalAction,
        help="use proxy"
    )
    parser.add_argument(
        "-k",
        "--keep-previous",
        action=argparse.BooleanOptionalAction,
        help="keep previous scan"
    )
    parser.add_argument(
        "-r404",
        "--required-404",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="only check urls that have a status/message 404 [default: True]"
    )

    tool_parser = parser.add_mutually_exclusive_group(required=True)
    tool_parser.add_argument(
        "-dir",
        action=argparse.BooleanOptionalAction,
        help="use dir search",
    )
    tool_parser.add_argument(
        "-crawler",
        action=argparse.BooleanOptionalAction,
        help="use only crawler",
    )

    return parser
