from config import config


async def export_urls(query, file_path):
    projection = {"url": 1, "_id": 0}

    results = await (
        config.mongo_database
        .discovered_urls
        .find(query, projection)
        .to_list(length=None)
    )

    with open(f"temp/{file_path}", "a+") as file:        
        urls = [u["url"] for u in results]
        file.write("\n".join(urls) + "\n")


async def manage_exporters():
    exporters = [
        {
            "exporter": config.export_status,
            "query": {"status": {"$in": config.export_status}},
            "file_path": "urls_by_status.txt"
        },
        {
            "exporter": config.export_content_type,
            "query": {"content_type": {"$in": config.export_content_type}},
            "file_path": "urls_by_content_type.txt"
        },
        {
            "exporter": config.export_regex,
            "query": {"url": {"$regex": config.export_regex}},
            "file_path": "urls_by_regex.txt"
        },
        {
            "exporter": config.export_urls,
            "query": {},
            "file_path": "urls.txt"
        },
        {
            "exporter": config.export_downloadable,
            "query": {"is_downloadable": True},
            "file_path": "downloadable.txt"
        }
    ]
    
    for exporter in exporters:
        if exporter["exporter"]:
            await export_urls(
                exporter["query"],
                exporter["file_path"]
            )