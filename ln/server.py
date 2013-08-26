'''Web server functions.'''

import json
import datetime
import dateutil.parser
from itertools import chain
from flask import Flask, request, make_response, jsonify, Response

from ln import __version__
from ln import backend
from ln.backend.base import Blob
from ln.backend.exception import BadTypeError, SeriesDoesNotExistError, \
    SeriesTimeOrderError


app = Flask('ln')
storage_backend = None


def jsonify_with_status_code(status_code, *args, **kwargs):
    response = jsonify(*args, **kwargs)
    response.status_code = status_code
    return response


def data_to_sse_stream(intial_times, initial_values, gen):
    '''Convert a generator of data into a generator of server-sent event
    messages.

    :param intial_times: Initial array of times for query
    :param intial_values: Initial array of series values
    :param gen: A generator of new (times, values) tuples
    '''
    for times, values in chain([(times, values)], gen):
        data = dict(times=[t.isoformat() for t in times], values=values)
        yield 'data: %s\n\n' % json.dumps(data)


@app.route('/')
def root():
    '''Get a list of data series.'''
    data = {
        'names': storage_backend.get_series_list()
    }

    return jsonify(data)


@app.route('/create', methods=['POST'])
def create():
    '''Create a new data series.'''
    f = request.form
    storage_backend.create_series(
            name=f['name'],
            type=f['type'],
            reduction=f['reduction'],
            interpolation=f['interpolation'],
            unit=f['unit'],
            description=f['description'],
            metadata=f['metadata']
            )

    data = {
        'result': 'ok'
    }

    return jsonify(data)


def make_url(series_name, index):
    return app.config['url_base'] + '/data/%s/%d' % (series_name, index)


@app.route('/data/<series_name>', methods=['GET', 'POST'])
def data(series_name):
    '''Get the original values recorded for this data series without
    resampling, or record a new value for this data series.
    '''
    if request.method == 'POST':
        try:
            time = dateutil.parser.parse(request.form['time'])
            if 'value' in request.files:
                value = request.files['value'].read()
            else:
                value = json.loads(request.form['value'])

            index = storage_backend.add_data(series_name, time, value)
            url = make_url(series_name, index)
            data = dict(index=index, url=url)
            return jsonify(**data)

        except SeriesDoesNotExistError as e:
            return jsonify_with_status_code(404)

        except SeriesTimeOrderError as e:
            data = dict(type='time_order', msg=str(e))
            return jsonify_with_status_code(400, **data)

        except BadTypeError as e:
            data = dict(type='bad_type', msg=str(e))
            return jsonify_with_status_code(400, **data)

    else:  # GET
        offset = request.args.get('offset', None)
        limit = request.args.get('limit', None)

        if offset is not None:
            offset = int(offset)
        if limit is not None:
            limit = int(limit)

        try:
            times, values, resume = storage_backend.get_data(series_name,
                                                             offset=offset,
                                                             limit=limit)
        except SeriesDoesNotExistError as e:
            return jsonify_with_status_code(404)

        data = dict(times=[t.isoformat() for t in times])

        if len(values) > 0 and isinstance(values[0], Blob):
            data['values'] = [make_url(series_name, b.index) for b in
                values]
        else:
            data['values'] = values

        if resume is not None:
            data['resume'] = resume
        return jsonify(**data)


@app.route('/data/<series_name>/<id>', methods=['GET'])
def get(series_name, id):
    '''Return just the value corresponding to a particular index number.
    Primarily used to fetch blobs.'''

    id = int(id)

    try:
        times, values, resume = storage_backend.get_data(series_name,
                                                         offset=id,
                                                         limit=1)
    except SeriesDoesNotExistError:
        return jsonify_with_status_code(404)

    if len(times) == 0:
        return jsonify_with_status_code(404)

    value = values[0]
    if isinstance(value, Blob):
        response = Response(mimetype=value.mimetype)
        response.set_data(value.get_bytes())
        return response
    elif hasattr(value, '__len__'):  # list-like
        return json.dumps(value.tolist())  # jsonify does not like non-dict
    else:
        return str(value)


@app.route('/data/<series_name>/config', methods=['GET', 'POST'])
def config(series_name):
    '''Get or modify configuration information for this data series. Only the
    unit and description of the series can be changed.
    '''
    if request.method == 'POST':
        try:
            unit = request.form['unit']
            description = request.form['description']
            metadata = request.form['metadata']
        except KeyError as e:
            data = {
                'result': 'fail',
                'msg': str(e)
            }

            return jsonify_with_status_code(400, **data)

        storage_backend.update_config(series_name, unit=unit,
                                      description=description,
                                      metadata=metadata)

        data = {
            'result': 'ok',
        }

        return jsonify(**data)

    else:  # GET
        config = storage_backend.get_config(series_name)
        if config is None:
            return make_response("Data series not found", 404)
        else:
            return jsonify(**config)


@app.route('/query')
def query():
    '''Resample the selected data series and return the result. The query
    engine may return results with slightly different first and last times, as
    well as a different number of points.

    If no end time is provided, the client will be send continuous updates via
    server-sent events.
    '''
    if 'last' not in request.args:
        continuous = True
        last = datetime.now().isoformat()
    else:
        continuous = False

    try:
        selectors = request.args.getlist('selector')
        first = request.args['first']
        last = request.args['last']
        npoints = int(request.args['npoints'])

    except Exception as e:
        data = dict(msg='invalid query: %s' % e)

        return jsonify_with_status_code(400, **data)

    if npoints < 2:
        data = dict(msg='npoints must be >= 2')

        return jsonify_with_status_code(400, **data)

    try:
        first_dt = dateutil.parser.parse(first)
        last_dt = dateutil.parser.parse(last)

        if first_dt >= last_dt:
            data = dict(msg='last time must be greater than first')

            return jsonify_with_status_code(400, **data)

    except ValueError as e:
        data = dict(msg='invalid ISO 8601 time specification: %s' % e)

        return make_response(json.dumps(data), 400)

    if not continuous:
        times, values = storage_backend.query(selectors, first_dt, last_dt, npoints)
        data = dict(times=[t.isoformat() for t in times], values=values)
        return jsonify(data)
    else:
        times, values, generator = \
            storage_backend.query_continuous(selectors, first, npoints)
        response_generator = data_to_sse_stream(times, values, generator)
        return Response(response_generator(), mimetype='text/event-stream')


def start(config):
    '''Start the web server.
    
    :param config: Configuration definition
    '''
    global storage_backend

    print('Natural Log', __version__)

    storage = config['storage']
    print('Opening "%s" storage backend...' % storage['backend'])
    storage_backend = backend.get_backend(storage)

    app.config['url_base'] = 'url_base'
    print('Base URL is', config['url_base'])

    app.run(host=config['host'], port=config['port'],
            threaded=True, debug=True)
