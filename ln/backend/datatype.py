'''Parse and represent natural log datatypes.'''

from ln.backend.exception import BadTypeError
import numpy as np

INT_TYPES = set(['int8', 'int16', 'int32', 'int64'])
FLOAT_TYPES = set(['float32', 'float64'])
SCALAR_TYPES = INT_TYPES | FLOAT_TYPES

NUMPY_TYPE_MAPPING = dict(
    int8=np.int8,
    int16=np.int16,
    int32=np.int32,
    int64=np.int64,
    float32=np.float32,
    float64=np.float64
)


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

    def is_int_scalar(self):
        '''Return true if this is an integer scalar type'''
        return self.base in INT_TYPES and self.shape is None \
            and self.mimetype is None

    def is_float_scalar(self):
        '''Return true if this is an floating point scalar type'''
        return self.base in FLOAT_TYPES and self.shape is None \
            and self.mimetype is None

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
        array = np.asarray(obj)
        return array.shape == self.shape

    def coerce(self, value):
        '''Convert ``value`` to the canonical Python type represent this
        datatype.

        Integer types go to ``int``, floating point types go to ``float``,
        array types go to numpy arrays with the corresponding dtype, and
        blob types become ``bytes``.

        Raises ``BadTypeError`` if ``value`` cannot be coerced to this
        datatype.
        '''
        try:
            if self.is_int_scalar():
                return int(value)
            elif self.is_float_scalar():
                return float(value)
            elif self.is_array():
                dtype = NUMPY_TYPE_MAPPING[self.base]
                array = np.asarray(value, dtype=dtype)
                if array.shape != self.shape:
                    raise BadTypeError('Cannot coerce value')
                return array
            elif self.is_blob():
                return bytes(value)
        except (ValueError, TypeError) as e:
            raise BadTypeError(str(e))

    def make_zero(self):
        '''Return an "zero" instance of this data type.

        Scalars return zero, array types return an array of the
        desired shape with all elements equal to zero, and blob
        types return the empty string.
        '''
        if self.is_int_scalar():
            return 0
        elif self.is_float_scalar():
            return 0.0
        elif self.is_array():
            return np.zeros(shape=self.shape, dtype=NUMPY_TYPE_MAPPING[self.base])
        elif self.is_blob():
            return b''

    def convert_to_jsonable(self, value):
        '''Converts value to a type that can be handled by the JSON parser,
        i.e. no numpy types.

        Assumes that input value has been returned by coerce, so is a scalar,
        numpy array, or bytes object.
        '''
        if self.is_int_scalar():
            return int(value)
        elif self.is_float_scalar():
            return float(value)
        elif self.is_array():
            return value.tolist()
        elif self.is_blob():
            return bytes(value)


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
