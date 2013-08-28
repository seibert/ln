__version__ = '0.1'

import platform
if platform.python_implementation() == 'PyPy':  # pragma: no cover
    import numpypy  # Allows all imports of numpy in rest of program
