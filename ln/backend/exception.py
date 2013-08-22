'''Backend exception hierarchy'''


class BackendError(Exception):
    '''Base exception for all problems with the backend.'''
    pass


class BadTypeError(BackendError):
    pass


class TimeOrderError(BackendError):
    pass
