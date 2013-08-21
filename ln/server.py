'''Web server functions.'''

from ln import __version__

def start(config):
    '''Start the web server.'''
    print 'Natural log', __version__

    storage = config['storage']
    print 'Opening "%s" storage backend...' % storage['backend']
    # open the backend
    backend = None

    print 'Base URL is', config['url_base']

    serve_forever(config['host'], config['port'], backend)


def serve_forever(host, port, backend):
    print 'Listening on %s:%i' % (host, port)

