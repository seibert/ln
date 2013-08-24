Data Series
============

A data series is a typed quantity that changes over time.  Each data series has a name, a data type, a default reduction strategy, and a default interpolation strategy.  Most data series are scalar types, such as integers and floating point values, but can also be array types or binary blobs.  Data series may also optionally have a unit, a description, or application-specific metadata.

Data Series Attributes
----------------------

Series Names
^^^^^^^^^^^^
The name of a series can be any sequence of alphanumeric characters, underscores, and periods.  We suggest the convention of organizing data series hierarchically with levels separated by periods.  For example, one could organize a set of temperature sensors this way::

    servers.node01.cpu_temp
    servers.node01.disk_temp
    servers.node02.cpu_temp
    servers.node02.disk_temp


.. _datatypes:

Data Types
^^^^^^^^^^
The type of a data series is used to determine the storage format for data in memory and on disk.  To save space, use a type appropriate to the range and precision of the data series.

Scalar Types
````````````

Data series with scalar types record a single number per update.  The valid scalar types are::

    int8
    int16
    int32
    int64
    float32
    float64

Note that the number at the end of the type refers to its length in *bits*.

Array Types
```````````

An array type is an n-dimensional array of values with identical scalar type.  Array types are a more compact way to record values that are typically accessed as a group, such as a list of numbered channels or a histogram.  Array types are specified with a scalar type followed by a shape specification in brackets.  The shape specification gives the size of each dimension separated by commas.  Examples::

  int16[100]
  float32[2,4]
  int32[10,10,2]

.. note:: Individual array elements cannot be recorded or queried separately.  If you frequently need to access array elements one at a time, consider splitting the elements into separately named data series.


Blob Types
``````````

A generic binary "blob" type is provided for variable length binary data which cannot be reasonably represented as a scalar or an array.  Blob data have very limited reduction and interpolation options, so scalar and array types should be used when practical.  Individual blob values for a data series will be given unique server URLs.  A blob type specification includes a MIME type which is returned to the HTTP client when the blob is retrieved.  Examples::

    blob:image/png
    blob:application/pdf
    blob:binary/octet-stream


Default Resampling Strategies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The handling of data points when resampling the time series in a query is controlled by a *reduction* and an *interpolation* strategy.  The reduction strategy specifies how to combine multiple points when they fall into a time interval, and the interpolation strategy specifies how to use adjacent intervals to set the value of a time interval when it contains no points.  These methods are described further in :ref:`reduction` and :ref:`interpolation`.

Although any strategy can be selected in the query (except in the case of blob types), many data series naturally fit only one pair of resampling strategies.  For this reason, when creating a data series, a default reduction and interpolation strategy must be selected.


Series Description, Unit and Metadata
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The description of a data series is an optional free-form text field that can be displayed in user-facing interfaces to Natural Log.  The unit describes the physical unit (kg, m, deg F, etc) of the values recorded for the data series.  The unit is not used for calculation purposes, but may also be shown to users in interfaces to Natural Log data.

The metadata field is another free-form text field that can be used for
specific applications.  Unlike the description field, the metadata field
should not be shown directly to users.  As an example, an array series that
holds the bins of a histogram can use the metadata field to store the bin
boundaries of the histogram for use by display applications.


.. _create-series:

Creating a Data Series
----------------------
We assume that you have the Natural Log server running as described in :ref:`server-config`.  The examples below use the `Requests <http://docs.python-requests.org/>`_ module for Python to make the REST API calls::

    import requests
    url_base = 'http://localhost:6283/'

To create a data series, we make a dictionary of the desired attributes and send it to the `create` URL.  Here is an example of creating a temperature data series::

    t = {
        'name' : 'node01.cpu_temp',
        'type' : 'float32',
        'reduction' : 'mean',
        'interpolation' : 'linear',
        'description' : 'Temperature of CPU in node01',
        'unit' : 'deg F'
    }

    r = requests.post(url_base + 'create/', data=t)
    assert r.status_code == 200  # Check for success

An integer commit counter::

    t = {
        'name' : 'commits',
        'type' : 'int8',
        'reduction' : 'sum',
        'interpolation' : 'middle',
        'description' : 'Number of commits to repository',
    }

    r = requests.post(url_base + 'create/', data=t)
    assert r.status_code == 200  # Check for success

An array data series::

    t = {
        'name' : 'channel_crc_errors',
        'type' : 'int32[100]',
        'reduction' : 'sum',
        'interpolation' : 'previous',
        'description' : 'Number of CRC errors for each data channel.',
    }

    r = requests.post(url_base + 'create/', data=t)
    assert r.status_code == 200  # Check for success

And finally, a blob data series::

    t = {
        'name' : 'cameras.entrance',
        'type' : 'blob:image/jpeg',
        'reduction' : 'middle',
        'interpolation' : 'none',
        'description' : 'Webcam aimed at lab entrance'
    }

    r = requests.post(url_base + 'create/', data=t)
    assert r.status_code == 200  # Check for success
