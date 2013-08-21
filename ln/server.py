'''Web server functions.'''

import json
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

    return ''


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

