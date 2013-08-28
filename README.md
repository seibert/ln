Natural Log
-----------

Natural Log (`ln` for short) is a time series database with a REST API.  The
database records time-varying scalars, arrays, and generic binary data at
irregularly-spaced intervals, and supports time-oriented queries on that data.
It is primarily intended for logging numeric data, rather than string messages
like syslog.

**WARNING:** Natural Log is currently practicing "Documentation Driven
Development," so none of the code exists to do any of this yet.


Requirements
------------

Natural Log requires:
  * Python 2.6, 2.7, 3.3 or PyPy 2.1
  * flask
  * requests
  * dateutil
  * argparse (only on Python 2.6)
  * numpy (or numpypy in the case of PyPy 2.1)


Documentation
-------------

The full documentation of Natural Log is at:

http://ln.rtfd.org


Development
-----------

Source code and issue tracker are found at GitHub:

http://github.com/seibert/ln

Continuous integration is provided by Travis-CI:

https://travis-ci.org/seibert/ln/builds


Authors
-------

Natural Log is developed by Stan Seibert and Andy Mastbaum.
