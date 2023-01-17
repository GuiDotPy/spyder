from utils.requester import check_urls, is_404
from crawler import crawl
from config import config
from utils.utils import split_host


def robots():
    pass


def sitemap():
    pass


def zip_urls(urls_by_domain):
    max_len = max(len(sublist) for sublist in urls_by_domain)
    zipped = []

    for i in range(max_len):
        zipped.append([
            url_list[i]
            for url_list in urls_by_domain
            if len(url_list) > i
        ])
    
    return zipped


def get_urls_by_domain(urls):
    urls_by_domain = {}

    for url in urls:
        urls_by_domain.setdefault(split_host(url), []).append(url)

    return list(urls_by_domain.values())


def add_dir(url_list, wordlist_chunk):
    return [
        f"{url}/{_dir}"
        for url in url_list
        for _dir in wordlist_chunk
    ]
 

def get_chunked_urls(urls_by_domain):
    return [
        url_list[i:i + config.max_concurrency]
        for url_list in zip_urls(urls_by_domain)
        for i in range(0, len(url_list), config.max_concurrency)
    ]


async def task_manager(urls):
    urls_by_domain = get_urls_by_domain(urls)

    with open("wordlists/dir_small.txt", 'r') as file:
        wl_length = sum(1 for _ in file)

    for url_list in get_chunked_urls(urls_by_domain):
        chuncked_wordlist = get_partial_wordlist((wl_length // len(url_list)) or 1)

        for chunk in chuncked_wordlist:
            responses = await check_urls(add_dir(url_list, chunk), redirect=True)

            urls = set(
                str(response.url)
                for response in responses
                if response
                and not is_404(response)
            )

            await crawl(urls)


def get_partial_wordlist(chunk_size):
    chunk = []
    
    with open("wordlists/dir_small.txt", 'r') as file:
        for line in file:
            chunk.append(line.strip())

            if len(chunk) == chunk_size:
                yield chunk
                chunk.clear()

        if chunk:
            yield chunk


async def filter_avaliable_404_pages(urls):
    urls_404 = [
        f"{url}/doesnt-exist-xyz"
        for url in urls
    ]

    responses = await check_urls(urls_404)

    avalible_urls = set()
    skipped_urls = set()

    for response in responses:
        if not response:
            continue

        url = str(response.request.url).replace("/doesnt-exist-xyz", "")

        if is_404(response):
            avalible_urls.add(url)
        else:
            skipped_urls.add(url)

    return avalible_urls, skipped_urls


async def search_dirs(urls):
    if config.required_404:
        urls, skipped_urls = await filter_avaliable_404_pages(urls)

        with open("temp/skipped_urls.txt", "a+") as file:
            file.write("\n".join(skipped_urls))

    if urls:
        await task_manager(urls)