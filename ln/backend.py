'''Storage backends.'''

def init(config):
    '''Initialize the storage backend.'''
    storage = config['storage']
    print 'Initializing "%s" storage backend...' % storage['backend']

    # do the stuff!

    print 'Done.'

