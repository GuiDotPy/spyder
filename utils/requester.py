import asyncio
import re
import ssl

import httpx
from rfc3986.exceptions import ResolutionError

from utils.views import print_result, Color
from config import config
from utils.utils import split_host, set_schema
from utils.exceptions import (
    CustomHttpxRequestNotRead,
    RateLimitExceeded
)


async def get_url(session, url):
    async with session.stream('GET', url) as response:
        response = CustomResponse(response)
        await response.aread()

        for response_handler in config.response_handlers:
            response = response_handler(response, config)

            if asyncio.iscoroutine(response):
                response = await response
            
            if not response:
                config.request_manager.done += 1
                print_result(url, message=Color("error").red)
                return None

    if is_404(response) and response.status_code != 404:
        response.status_code = 404

    return response


async def do_request(url, session, semaphore):
    for _ in range(config.max_timeout + 1):
        try:
            async with semaphore:
                response = await get_url(session, url)

            if not response:
                return None

            config.request_manager.done += 1
            config.request_manager.reset()

            print_result(
                url=response.request.url,
                status=response.status_code,
                valid=True,
                message=Color("ok").green
            )

            return response
        except httpx.TimeoutException:
            print_result(url, message=Color("timeout").yellow)
        except RateLimitExceeded:
            message = "rate limit exceeded"
            break
        except (httpx.HTTPError, ResolutionError, ssl.SSLError, ValueError):
            message = "error"
            break
    else:
        message = "max timeout"

    config.request_manager.done += 1
    print_result(url, message=Color(message).red)
    return None


async def rate_limit_handler(semaphore, url, status_code):
    pass # soon


def is_url_in_scope(url):
    url = set_schema(url)
    host = split_host(url)

    if not host or host not in config.scope_domains:
        return None

    if config.scope_regex and not re.fullmatch(config.scope_regex, url):
        return None

    return url[:300]


def is_404(response):
    if not response:
        return False

    if response.status_code == 404:
        return True

    messages_404 = (
        "page not found",
        "404 not found",
        "404 error",
        "error code: 404",
        "error-404",
        "the requested resource could not be found",
        "file or directory not found",
        "the page you are looking for could not be found",
        "the requested url was not found on this server",
        "error: page not found",
        "oops! this page could not be found",
        "the page you requested was not found",
        "the requested resource could not be located"
    )

    for msg in messages_404:
        if msg in response.text.lower():
            return True

    if response.history:
        path = response.url.path

        if not path or path == "/":
            return True

    return False


async def check_urls(urls, redirect=False):
    single_url = False

    if isinstance(urls, str):
        single_url = True
        urls = [urls]

    semaphore = asyncio.BoundedSemaphore(config.max_concurrency)
    config.request_manager.done = 0
    config.request_manager.total = len(urls)

    session = httpx.AsyncClient(
        follow_redirects=redirect,
        headers=config.headers,
        verify=False,
        proxies=config.proxies
    )

    reqs = [
        do_request(
            url=url,
            session=session,
            semaphore=semaphore
        )
        for url in urls
    ]

    if single_url:
        return await reqs[0]

    return await asyncio.gather(*reqs)


class CustomResponse:
    def __init__(self, httpx_response):
        self.httpx_response = httpx_response
        self.url = httpx_response.url
        self.headers = httpx_response.headers
        self.request = httpx_response.request
        self.status_code = httpx_response.status_code
        self.history = httpx_response.history

    def __repr__(self):
        reason_phrase = self.httpx_response.reason_phrase
        return f"<Response [{self.status_code} {reason_phrase}]>"

    @property
    def text(self):
        if not hasattr(self, "_text"):
            raise CustomHttpxRequestNotRead()
        
        return self._text

    @property
    def is_media(self):
        mime_types = (
            "audio",
            "image",
            "video",
            "font",
            "application/pdf"
        )

        for mime_type in mime_types:
            if mime_type in self.headers.get("content-type", ""):
                return True

        if self.url.path.endswith(config.file_extensions):
            return True

        return False

    @property
    def is_binary(self):
        conditions = (
            "application/octet-stream" in self.headers.get("content-type", ""),
            "attachment" in self.headers.get("content-disposition", ""),
            int(self.headers.get("content-length", 0)) > 10_000_000
        )

        if any(conditions):
            return True

        return False

    @property
    def is_downloadable(self):
        return self.is_binary and not self.is_media

    async def aread(self):
        self._text = ""

        if self.is_media or self.is_binary:    
            return self._text

        async for chunk in self.httpx_response.aiter_text():
            self._text += chunk

            if self.httpx_response.num_bytes_downloaded >= 3_000_000:
                break

        return self._text