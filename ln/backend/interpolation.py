'''Functions that perform the different interpolation strategies.'''


def none(reduced_values, datatype, center_times):
    return reduced_values


def zero(reduced_values, datatype, center_times):
    new_reduced_values = []
    for v in reduced_values:
        if v is not None:
            new_reduced_values.append(v)
        else:
            new_reduced_values.append(datatype.make_zero())
    return new_reduced_values


def previous(reduced_values, datatype, center_times):
    new_reduced_values = []
    last_seen = None
    for v in reduced_values:
        if v is not None:
            last_seen = v
            new_reduced_values.append(v)
        else:
            new_reduced_values.append(last_seen)
    return new_reduced_values


def linear(reduced_values, datatype, center_times):
    pass


INTERPOLATIONS = dict(none=none, zero=zero, previous=previous, linear=linear)
