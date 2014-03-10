import json
import ln
from ln.backend.compat import zip
from base64 import b64encode


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
            transform = lambda v: b64encode(v.get_bytes())
        else:
            transform = lambda v: v

        times, values, resume = backend.get_data(series_name, 0)
        points = [(str(time), transform(value))
            for time, value in zip(times, values)]
        obj['series'].append(dict(config=config, points=points))

    json.dump(obj, output_file)
