'''Web server functions.'''

import json
import dateutil.parser
from flask import Flask
from flask import request
from ln import __version__
from ln import backend

app = Flask('ln')
storage_backend = None

@app.route('/')
def root():
    '''Get a list of data sources.'''
    data = {
        'names': storage_backend.get_data_source_list()
    }

    return json.dumps(data)


@app.route('/create', methods=['POST'])
def create():
    '''Create a new data source.'''
    f = request.form
    storage_backend.create_data_source(f['name'], f['type'], f['reduction'],
                                       f['interpolation'], f['unit'],
                                       f['description'])

    data = {
        'result': 'ok'
    }

    return json.dumps(data)


@app.route('/data/<source_name>', methods=['GET', 'POST'])
def data(source_name):
    '''Get the original values recorded for this data source without
    resampling, or record a new value for this data source.
    '''
    if request.method == 'POST':
        try:
            index, url = storage_backend.add_data(source_name, time, value)

            data = {
                'index': index
            }

            if url is not None:
                data['url'] = url

            return json.dumps(data)

        except TimeOrderError, e:
            data = {
                'type': 'time_order',
                'msg': e
            }

            return make_response(json.dumps(data), 400)

        except BadTypeError, e:
            data = {
                'type': 'bad_type',
                'msg': e
            }

            return make_response(json.dumps(data), 400)

    else:  # GET
        offset = request.args.get('offset', None)
        limit = request.args.get('limit', None)
        times, values, resume = storage_backend.get_data(source_name,
                                                         offset=offset,
                                                         limit=limit)

        data = {
            'times': times,
            'values': values,
        }

        if resume is not None:
            data['resume'] = resume

        return json.dumps(data)


@app.route('/data/<source_name>/config', methods=['GET', 'POST'])
def config(source_name):
    '''Get or modify configuration information for this data source. Only the
    unit and description of the source can be changed.
    '''
    if request.method == 'POST':
        try:
            unit = request.form['unit']
            description = request.form['description']
        except KeyError, e:
            data = {
                'result': 'fail',
                'msg': e
            }

            return make_response(json.dumps(data), 400)

        storage_backend.update_config(source_name, unit=unit,
                                      description=description)

        data = {
            'result': 'ok',
        }

        return json.dumps(data)

    else:  # GET
        config = storage_backend.get_config(source_name)

        return json.dumps(config)


@app.route('/query')
def query():
    '''Resample the selected data sources and return the result. The query
    engine may return results with slightly different first and last times, as
    well as a different number of points.
    '''
    try:
        selectors = request.form['selectors']
        first = request.form['first']
        last = request.form['last']
        npoints = int(request.form['npoints'])

    except Exception, e:
        data = {
            'msg': 'invalid form input: %s' % e
        }

        return make_response(json.dumps(data), 400)

    if npoints < 2:
        data = {
            'msg': 'npoints must be >= 2'
        }

        return make_response(json.dumps(data), 400)

    try:
        first_dt = dateutil.parser.parse(request.form['first'])
        last_dt = dateutil.parser.parse(request.form['last'])

        if first_dt >= last_dt:
            data = {
                'msg': 'last time must be greater than first'
            }

            return make_response(json.dumps(data), 400)

    except ValueError, e:
        data = {
                'msg': 'invalid ISO 8601 time specification: %s' % e
        }

        return make_response(json.dumps(data), 400)

    times, values = storage_backend.query(selectors, first, last, npoints)

    data = {
        'times': times,
        'values': values
    }

    return json.dumps(data)


def start(config):
    '''Start the web server.
    
    :param config: Configuration definition
    '''
    global storage_backend 

    print 'Natural log', __version__

    storage = config['storage']
    print 'Opening "%s" storage backend...' % storage['backend']
    storage_backend = backend.get_backend(storage)

    print 'Base URL is', config['url_base']

    app.run(host=config['host'], port=config['port'], debug=True)

