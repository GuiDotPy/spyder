import os
from urllib.parse import urlparse


def split_host(url):
    try:
        parsed_url = urlparse(url)
        
        if parsed_url.port:
            return f"{parsed_url.hostname}:{parsed_url.port}"
        
        return parsed_url.hostname
    except ValueError:
        return None


def get_urls_from_responses(responses):
    return set(
        str(response.url)
        for response in responses
        if response
    )


def set_schema(url):
    if not url.startswith(("https://", "http://")):
        url = f"https://{url}"
    
    return url


def remove_params(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{split_host(url)}{parsed_url.path}"


def create_or_clear_temp(base_dir):
    path =  f"{base_dir}/temp"
    
    if not os.path.isdir(path):
        os.makedirs(path)
        
    for file in os.listdir(path):
        os.remove(f"{path}/{file}")


def get_chuncked_list(_list, length):
    return [
        list(_list)[i:i+length]
        for i in range(0, len(_list), length)
    ]
