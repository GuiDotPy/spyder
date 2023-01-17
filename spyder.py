import asyncio

from pymongo.errors import ServerSelectionTimeoutError
from dotenv import load_dotenv

from dir_search import search_dirs
from crawler import crawl
from config import config, selected_command
from utils.databases import set_collections, delete_collections
from utils.exporters import manage_exporters
from utils.utils import create_or_clear_temp


load_dotenv()


async def manage_previous_scan():
    if config.keep_previous:
        return

    create_or_clear_temp(config.base_dir)
    await delete_collections()


async def scan():
    if not config.stdin:
        return

    await set_collections()
    await manage_previous_scan()

    if config.dir:
        await search_dirs(config.stdin)

    if config.crawler and not config.dir:
        await crawl(config.stdin)


async def main():
    positional_commands = {
        "scan": scan,
        "exporter": manage_exporters
    }
    
    await positional_commands[selected_command]()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
        print("\nbye")
    except ServerSelectionTimeoutError:
        print("install and run MongoDb before run this tool")
