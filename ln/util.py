import json
from base64 import b64encode

import ln
from ln import backend
from ln.backend.compat import zip


def export_json(backend, output_file):
    '''Serialize the entire contents of ``backend`` in JSON format to the
    file object ``output_file``.'''
    obj = {
        'version': ln.__version__,
        'series': []
    }

    for series_name in backend.get_series_list():
        config = backend.get_config(series_name)
        if config['type'].startswith('blob'):
            transform = lambda v: b64encode(v.get_bytes()).decode('utf-8')
        else:
            transform = lambda v: v

        times, values, resume = backend.get_data(series_name, 0)
        points = [(str(time), transform(value))
            for time, value in zip(times, values)]
        obj['series'].append(dict(config=config, points=points))

    json.dump(obj, output_file)


def export_command(config, options):
    '''Export database to JSON file.'''
    print('Natural Log', ln.__version__)

    storage = config['storage']
    print('Opening "%s" storage backend...' % storage['backend'])
    storage_backend = backend.get_backend(storage)

    with open(options.output) as output:
        export_json(storage_backend, output)
