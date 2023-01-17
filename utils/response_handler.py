from urllib.parse import urlparse
from utils.exceptions import RateLimitExceeded


def skip_responses(response, config):
    if response.status_code in config.skip_status:
        return None

    for text in config.skip_text:
        if text in response.text:
            return None

    for text in config.skip_urls:
        if text in str(response.url):
            return None

    return response


def is_too_many_requets(response, config):
    status = response.status_code
    rate_limit_status = config.request_manager.rate_limit_status

    if status == 429:
        raise RateLimitExceeded("too many requests", 429)

    if str(status) in rate_limit_status.keys():
        pass # comming soon

    return response


def skip_http_errors(response, config):
    error_count = config.request_manager.error_count_per_domain
    rate_limit_status = config.request_manager.rate_limit_status

    url = urlparse(str(response.url))
    domain = url.hostname
    status = str(response.status_code)

    if status.startswith("5"):
        return None

    if status == "404" or status in rate_limit_status:
        return response

    if status.startswith("4"):
        current_count = error_count.get(domain, {}).get(status, 0)
        error_count.setdefault(domain, {})[status] = current_count + 1

        if error_count[domain][status] >= 25:
            return None

    return response