from config import config


async def set_collections():
    current_collections = await config.mongo_database.list_collection_names()

    collections = (
        "visited_urls",
        "discovered_urls",
    )

    for collection in collections:
        if collection in current_collections:
            continue
        
        await config.mongo_database.create_collection(collection)
        config.mongo_database[collection].create_index('url')


async def delete_collections():
    collections = await config.mongo_database.list_collection_names()

    for collection in collections:
        config.mongo_database[collection].delete_many({})