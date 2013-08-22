'''Parse and represent natural log datatypes.'''

from ln.backend.exception import BadTypeError
import numpy as np

SCALAR_TYPES = set(['int8', 'int16', 'int32', 'int64', 'float32', 'float64'])

class Datatype(object):
    '''A representation of a Natural Log datatype'''

    def __init__(self, base, shape=None, mimetype=None):
        '''Create a new datatype.

        :param base: Base data type, either one of the scalar types or 'blob'.
        :param shape: Tuple of dimensions if array type, otherwise None.
        :param mimetype: Mimetype of data if blob type, otherwise None.

        Raises BadTypeError if an invalid combination of arguments is set.
        '''
        if base not in SCALAR_TYPES and base != 'blob':
            raise BadTypeError('Base of type must be one of the scalar types or "blob".')
        if shape is not None and mimetype is not None:
            raise BadTypeError('A type cannot have array shape and mimetype at the same time.')
        if base == 'blob' and mimetype is None:
            raise BadTypeError('A blob type must have a MIME type.')

        self.base = base
        if shape is not None:
            self.shape = tuple(shape)  # Ensure equality tests work later
        else:
            self.shape = None
        self.mimetype = mimetype

    def is_scalar(self):
        '''Return true if this is a scalar type'''
        return self.shape is None and self.mimetype is None

    def is_array(self):
        '''Return true if this is an array type.'''
        return self.shape is not None

    def is_blob(self):
        '''Return true if this is a blob type'''
        return self.base == 'blob'

    def check_shape(self, obj):
        '''Check the shape of object matches this data type (only valid for
        array types).

        Works on numpy arrays or nested lists / tuples.

        Returns True if shapes match.
        '''
        array = np.array(obj)
        return array.shape == self.shape


def parse_datatype(typestring):
    '''Parse a datatype string and return an instance of Datatype to
    represent it.

    :param typestring: String descriptor of data type.
    '''

    if ':' in typestring:  # Attempt to parse as blob type
        base, mime = typestring.split(':', 1)
        if base != 'blob':
            raise BadTypeError('Only blob types can contain ":"')
        else:
            return Datatype('blob', mimetype=mime)
    elif '[' in typestring:  # Attempt to parse as array type
        base, rest = typestring.split('[', 1)
        if base not in SCALAR_TYPES:
            raise BadTypeError('Invalid base type in array type')
        shape_string = rest.split(']', 1)[0].split(',')
        try:
            # Convert string to tuple of integers, removing whitespace
            shape = tuple([int(s.strip()) for s in shape_string
                if s.strip() != ''])
        except ValueError:
            raise BadTypeError('Invalid shape in array type')

        return Datatype(base, shape=shape)
    else:
        if typestring not in SCALAR_TYPES:
            raise BadTypeError('Unknown scalar type')
        else:
            return Datatype(typestring)
