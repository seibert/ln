.. _recording-data:

Recording Data
==============

Natural Log is designed as an append-only database.  The values for a given data source must be recorded in chronological order, and cannot be modified later.  We may relax these restrictions eventually, but for now inserting, removing or modify points requires replaying points from one data source into another one.

The examples in this section assume the Natural Log server is running with the configuration described in :ref:`server-config` and the the data sources described in :ref:`create-source`.  We continue to use the `Requests <http://docs.python-requests.org/>`_ module::

    import requests
    url_base = 'http://localhost:6283/'


Server-side Timestamping
------------------------
Recording data is done by POST requests to the `data/[source name]/` URL.  If no time is given, then the time of the request is used as the time of the data point.  This avoids the need to worry about time synchronization on data collection clients.

Here is an example that populate the temperature data source with some random values by pausing between each point::

    import time, random
    post_url = url_base + 'data/node01.cpu_temp/'
    for i in xrange(10):
        v = { 'value' : str(random.uniform(80, 120)) }
        r = requests.post(post_url, data=v)
        assert r.status_code == requests.codes.ok  # Check for errors


Client-side Timestamping
------------------------
A timestamp can also be provided with the data point.  The restriction is that each data source is append-only, so data must always be sent to the database in chronological order.

To avoid ambiguity, the interface of Natural Log describes times in ISO 8601 format, and times are always in UTC.  Here is an example::

    post_url = url_base + 'data/commits/'
    for i in xrange(1, 15):
        v = {
            'time'  : '2013-07-%02d 12:00:31.503' % i,
            'value' : '1'
        }
        r = requests.post(post_url, data=v)
        assert r.status_code == requests.codes.ok  # Check for errors


Array Data Sources
------------------
Sources with array data types are updated in the same way, just with value set to a JSON string representation of a list. Here is an example with the CRC error data source::

    import json
    post_url = url_base + 'data/channel_crc_errors/'
    channel_data = [ 1 for i in xrange(100) ]
    v = { 'value' : json.dumps(channel_data) }
    r = requests.post(post_url, data=v)
    assert r.status_code == requests.codes.ok  # Check for errors

Multi-dimensional arrays can be represented with nested lists of lists.


Blob Data Sources
-----------------
Blob data sources are handled slightly differently in order to transmit binary data.  We have to use a multipart form encoding to hold the value field.  In Requests, this is very straightforward::

    # First fetch Google's Euler doodle image
    r = requests.get('http://lh5.ggpht.com/Npa8E2JNHZHzrfQCutzmqqxD3WyQiiLibcaAvR4rR0hEs7LJDY-ahWf5SRBN5Jj7oDhRiZKk7Ca_rCn4rEAEFt_HC3Ho2OImBYDZKPg')
    assert r.status_code == requests.codes.ok
    image = r.content

    # Next, upload
    post_url = url_base + 'data/cameras.entrance/'
    import datetime
    t = { 'time' : datetime.utcnow().isoformat(' ') }
    v = { 'value' : image }
    r = requests.post(post_url, data=t, files=v)
    assert r.status_code = requests.codes.ok
