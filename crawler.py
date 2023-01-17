from urllib.parse import urljoin, urlparse
import re

from utils.requester import check_urls, is_404, is_url_in_scope
from config import config
from utils.utils import get_urls_from_responses, get_chuncked_list


async def get_urls_not_in_collection(collection, urls):
    not_in_collection = set()

    for urls_chunk in get_chuncked_list(urls, 5000):
        db_urls = collection.find(
            filter={'url': {'$in': list(urls_chunk)}},
            projection={"url": 1, "_id": 0}
        )
        
        db_urls = set(
            u["url"]
            for u in await db_urls.to_list(length=None)
        )

        not_in_collection.update(set(urls_chunk) - db_urls)

    return not_in_collection


async def save_visited_urls(urls):
    collection = config.mongo_database.visited_urls
 
    for url in urls:
        if not await collection.find_one({"url": url}):
            await collection.insert_one({"url": url})


def get_links(url, html):
    urls_regex = (
        r"https?:\\?/\\?/[a-zA-Z0-9-.]+\.[a-zA-Z]+(?::[0-9]{1,5})?(?:\\?/[a-zA-Z0-9-._%]+)*\\?/?",
        r"['\"]((?:\.{0,2}\\?/[a-zA-Z0-9-._%]+)+\\?/?)['\"]",
        r"(?:href|src|action)\s*=\s*['\"](.+?)['\"]"
    )

    urls = set()

    for regex in urls_regex:
        for match in re.findall(regex, html):
            new_url = is_url_in_scope(urljoin(url, match))

            if new_url:
                urls.add(new_url.split("?")[0])

    return urls


async def recursive_dir_search(urls):
    new_urls = set()

    for url in urls:
        paths = urlparse(url).path.split("/")

        new_urls.update(
            urljoin(url, "/".join(paths[:i]))
            for i in range(len(paths))
            if paths[:i]
        )
    
    responses = await check_urls(urls=new_urls - urls, redirect=True)

    return [
        response
        for response in responses
        if response and not is_404(response)
    ]


async def do_crawl(urls):
    urls_found = set()
    valid_responses = []

    responses = await check_urls(urls=urls, redirect=True)

    if len(responses) > 500:
        print("\nsaving...")

    for response in responses:
        if response and not is_404(response):
            valid_responses.append(response)

            if not response.is_media and not response.is_binary:
                urls_found.update(get_links(str(response.url), response.text))

    return urls_found, valid_responses


async def save_valid_responses(valid_responses):
    collection = config.mongo_database.discovered_urls
    saved_urls = set()
    response_data = []

    urls_not_in_collection = await get_urls_not_in_collection(
        collection=collection,
        urls=get_urls_from_responses(valid_responses)
    )
    
    for response in valid_responses:
        url = str(response.url)

        if url not in saved_urls and url in urls_not_in_collection:
            response_data.append(
                {
                    "url": url,
                    "status": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "is_downloadable": response.is_downloadable
                }
            )
  
        saved_urls.add(url)

    if response_data:
        await collection.insert_many(response_data)
        return saved_urls
    
    return []


async def crawl(unvisited_urls):
    for _ in range(config.max_recrawl + 1):
        next_urls = set()

        for unvisited_urls_chunk in get_chuncked_list(unvisited_urls, 10_000):
            urls_found, valid_responses = await do_crawl(unvisited_urls_chunk)
 
            valid_responses.extend(
                await recursive_dir_search(
                    get_urls_from_responses(valid_responses)
                )
            )

            new_urls = await get_urls_not_in_collection(
                collection=config.mongo_database.visited_urls,
                urls=urls_found
            )

            await save_visited_urls(unvisited_urls_chunk)
            await save_valid_responses(valid_responses)

            next_urls.update(new_urls)
            
        unvisited_urls = new_urls