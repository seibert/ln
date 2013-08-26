'''Backend exception hierarchy'''


class BackendError(Exception):
    '''Base exception for all problems with the backend.'''
    pass


class BadTypeError(BackendError):
    pass


class BadSelectorError(BackendError):
    pass


class TimeOrderError(BackendError):
    pass


class SeriesCreationError(BackendError):
    pass


class SeriesDoesNotExistError(BackendError):
    pass


class SeriesTimeOrderError(BackendError):
    pass
