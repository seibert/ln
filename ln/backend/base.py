'''Storage backends.'''

class DataSource(object):
    '''A source of data to log.'''
    def __init__(self, name, type, reduction, interpolation, unit,
            description):
        self.name = name
        self.type = type
        self.reduction = reduction
        self.interpolation = interpolation
        self.unit = unit
        self.description = description


class Backend(object):
    '''A storage backend interface.'''
    def __init__(self):
        pass

    def get_data_source_list(self):
        raise Exception('Cannot call get_data_source_list on base class.')

    def create_data_source(self, name, type, reduction, interpolation, unit,
            description):
        raise Exception('Cannot call create_data_source on base class.')


class DictBackend(Backend):
    '''A storage backend implemented with a dict.
    
    For development use only!
    '''
    def __init__(self):
        self.data = {}

    def get_data_source_list(self):
        return self.data.keys()

    def create_data_source(self, name, type, reduction, interpolation, unit,
            description):
        self.data[name] = DataSource(name, type, reduction, interpolation,
                                     unit, description)


def init(config):
    '''Initialize the storage backend.
    
    :param config: Configuration definition
    '''
    storage = config['storage']
    print 'Initializing "%s" storage backend...' % storage['backend']

    # do the stuff!

    print 'Done.'


def get_backend(storage_config):
    '''Find/build a backend based on the configuration.
    
    :param config: storage section of the configuration
    '''
    storage_type = storage_config['backend']
    if storage_type == 'memory':
        return DictBackend()

