'''Web server functions.'''

import json
import datetime
import dateutil.parser
from flask import Flask
from flask import request, make_response, Response
from ln import __version__
from ln import backend

app = Flask('ln')
storage_backend = None

def data_to_sse_stream(gen):
    '''Convert a generator of data into a generator of server-sent event
    messages.

    :param gen: A generator of (time, value) tuples
    '''
    for t, v in gen:
        data = {
            'time': t,
            'value': v
        }

        yield 'data: %s\n\n' % json.dumps(data)


@app.route('/')
def root():
    '''Get a list of data series.'''
    data = {
        'names': storage_backend.get_series_list()
    }

    return json.dumps(data)


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

    return json.dumps(data)


@app.route('/data/<series_name>', methods=['GET', 'POST'])
def data(series_name):
    '''Get the original values recorded for this data series without
    resampling, or record a new value for this data series.
    '''
    if request.method == 'POST':
        try:
            index, url = storage_backend.add_data(series_name, time, value)

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
        times, values, resume = storage_backend.get_data(series_name,
                                                         offset=offset,
                                                         limit=limit)

        data = {
            'times': times,
            'values': values,
        }

        if resume is not None:
            data['resume'] = resume

        return json.dumps(data)


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
        except KeyError, e:
            data = {
                'result': 'fail',
                'msg': str(e)
            }

            return make_response(json.dumps(data), 400)

        storage_backend.update_config(series_name, unit=unit,
                                      description=description,
                                      metadata=metadata)

        data = {
            'result': 'ok',
        }

        return json.dumps(data)

    else:  # GET
        config = storage_backend.get_config(series_name)
        if config is None:
            return make_response("Data series not found", 404)
        else:
            return json.dumps(config)


@app.route('/query')
def query():
    '''Resample the selected data series and return the result. The query
    engine may return results with slightly different first and last times, as
    well as a different number of points.

    If no end time is provided, the client will be send continuous updates via
    server-sent events.
    '''
    if 'first' in request.form:
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

    else:
        try:
            selectors = request.form['selectors']
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
            last_dt = datetime.utcnow()

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

        generator = storage_backend.query_continuous(selectors, first, npoints)

        response_generator = data_to_sse_stream(generator)

        return flask.Response(response_generator(),
                              mimetype='text/event-stream')


def start(config):
    '''Start the web server.
    
    :param config: Configuration definition
    '''
    global storage_backend

    print 'Natural Log', __version__

    storage = config['storage']
    print 'Opening "%s" storage backend...' % storage['backend']
    storage_backend = backend.get_backend(storage)

    print 'Base URL is', config['url_base']

    app.run(host=config['host'], port=config['port'],
            threaded=True, debug=True)
