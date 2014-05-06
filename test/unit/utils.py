import json

def get_config_urls(filename=None):
    if filename is None:
        filename = 'default.json'

    config = None
    with open(filename, 'r') as f:
        config = json.load(f)

    return config['host'], config['port'], config['url_base']

