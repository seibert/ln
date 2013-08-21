Server Installation and Setup
=============================

The fastest way to install Natural Log and its dependencies is with virtualenv/pip::

    virtualenv ln_env
    source ln_env/bin/activate
    cd ln_env
    pip install ln

The included REST server is built with the `Flask microframework <http://flask.pocoo.org/>`_.


.. _server-config:

Configuring the Server
----------------------
Once Natural Log is installed, you need to create a server configuration file, which uses the JSON format.  Here is an example ``ln_local.json`` config file for a local test server we will use elsewhere in the documentation::

    {
        "host" : "127.0.0.1",
        "port" : 6283,
        "url_base" : "http://localhost:6823/",

        "resampling_intervals" : [1, 60, 3600, 86400],

        "storage" : {
                        "backend" : "memory"
                    }
    }

The required fields in the server configuration are:

==========================  ===============  ======================
Field Name                  JSON Type        Description
==========================  ===============  ======================
``host``                    String           IP address to which to bind
``port``                    Number           Port number to which to listen
``url_base``                String           Base URL for this server.  Used to construct URLs for responses.
``resampling_intervals``    List of numbers  The server will resample data with these intervals (in seconds).
``storage``                 Object           An object describing the storage backend to use.  See :ref:`backends` for more details.
==========================  ===============  ======================


.. _backends:

Storage Backends
----------------
Natural Log supports multiple storage backends as a way to experiment with different ways to store time series data.  Each backend and its configuration parameters are described below.


In-memory Backend
^^^^^^^^^^^^^^^^^
This backend stores all data in memory, so **memory usage will grow without bound** and **all data is lost when the server is shutdown**.  The in-memory backend is intended for testing and development purposes only.  Do not ever use this backend on a production deployment!  The storage configuration fields are:

==========================  ===============  ======================
Field Name                  JSON Type        Description
==========================  ===============  ======================
``backend``                 String           Set to ``memory``
==========================  ===============  ======================


SQLite
^^^^^^
This backend stores the data in an SQLite file.  Data is saved to disk and SQLite's ACID guarantees make this a production-worthy option.  It is not particularly fast.

==========================  ===============  ======================
Field Name                  JSON Type        Description
==========================  ===============  ======================
``backend``                 String           Set to ``sqlite``
``filename``                String           Name of sqlite file on disk.
==========================  ===============  ======================


Starting the Server
-------------------
Before starting the Natural Log server, we first need to initialize the storage backend::

    $ ln-server -c ln_local.json init
    Natural Log 0.1
    Initializing "memory" storage backend...
    Done.

Then we can start the server::

    $ ln-server -c ln_local.json start
    Natural Log 0.1
    Opening "memory" storage backend...
    Listening on 127.0.0.1:6283
    Base URL is http://localhost:6283/


