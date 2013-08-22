REST API Reference
==================


``GET /``
---------
Get a list of data sources.

URL Options
^^^^^^^^^^^
None

Response
^^^^^^^^
Format: *JSON*

==========  ================  ==============================================
Field name  Type              Description
==========  ================  ==============================================
``names``   List of strings   Names of all data sources known to this server
==========  ================  ==============================================


``POST /create/``
-----------------
Create a new data source.

Request
^^^^^^^
Format: *Form encoded*

=================  =================  ==============================================
Field name         Type               Description
=================  =================  ==============================================
``name``           String             Name of this data source.  Example: ``servers.node01.cpu_temp``
``type``           String             Type of this data source.  See :ref:`datatypes` for more information.
``reduction``      String             Name of reduction strategy.  See :ref:`reduction` for more information.
``interpolation``  String             Name of interpolation strategy. See :ref:`interpolation` for more information.
``unit``           String             Unit of measure.  May be empty string.
``description``    String             Description of data source.  May be empty string.
=================  =================  ==============================================


``GET /data/[source name]/``
----------------------------
Get the original values recorded for this data source, without resampling.

URL Options
^^^^^^^^^^^

==============  ==============================================
Parameter Name  Description
==============  ==============================================
``offset``      Index number of data point to start with
``limit``       Maximum number of points to return.  Server may impose a smaller maximum.
==============  ==============================================

If ``offset`` and ``limit`` are not set in the URL, then by default the server
will return the last recorded value for the data source.

Response (200)
^^^^^^^^^^^^^^
Format: *JSON*

==========  =================  ==============================================
Field name  Type               Description
==========  =================  ==============================================
``times``   List of strings    List of ISO 8601 timestamps for all values.
``values``  List of ??         List of recorded values for this data source.
``resume``  Number (optional)  If maximum # of returned values reached, this is the value to pass to the ``offset`` parameter on the next ``GET`` call to continue.
==========  =================  ==============================================


``POST /data/[source name]/``
-----------------------------
Record a new value for this data source.

Request
^^^^^^^
Format: *Form encoded or multipart form encoded*

==========  =================  ==============================================
Field name  Type               Description
==========  =================  ==============================================
``time``    String (optional)  ISO 8601 timestamp for value.  If omitted, the server will use the time of the POST as the time of the value.
``value``   Various            JSON-encoded new value, either as a number for scalar data sources, or a list of numbers (or a list of lists of numbers, etc) for array types.
==========  =================  ==============================================

If this data source is a blob type, the request should be multipart-encoded with ``value`` attached as a file.  The MIME type of the encoded file in the POST request will be ignore in favore of the MIME type that was specified when the data source was created.

Response: Success (200)
^^^^^^^^^^^^^^^^^^^^^^^
Format: *JSON*

Success.

==========  =================  ==============================================
Field name  Type               Description
==========  =================  ==============================================
``index``   Number             ID number of newly recorded data point.  Can be used as an offset to retrieve it later.
``url``     String (optional)  If a blob data source, the URL for the newly recorded binary data.
==========  =================  ==============================================

Response: Failure (400)
^^^^^^^^^^^^^^^^^^^^^^^
Format: *JSON*

Failure can occur if:
* The timestamp for the data point is actually before the last recorded data point (``time_order``).
* The POSTed value does not match the data type of the source or has the wrong dimensions for array types.

==========  =================  ==============================================
Field name  Type               Description
==========  =================  ==============================================
``type``    String             Type of failure: "time_order", "bad_type"
``msg``     String             A short explanation of the error.
==========  =================  ==============================================


``GET /data/[source name]/config/``
-----------------------------------
Get the configuration information for this data source.

Response (200)
^^^^^^^^^^^^^^
Format: *JSON*

=================  =================  ==============================================
Field name         Type               Description
=================  =================  ==============================================
``name``           String             Name of this data source.  Example: ``servers.node01.cpu_temp``
``type``           String             Type of this data source.  See :ref:`datatypes` for more information.
``reduction``      String             Name of reduction strategy.  See :ref:`reduction` for more information.
``interpolation``  String             Name of interpolation strategy. See :ref:`interpolation` for more information.
``unit``           String             Unit of measure.  May be empty string.
``description``    String             Description of data source.  May be empty string.
=================  =================  ==============================================


``POST /data/[source name]/config/``
------------------------------------
Modify the configuration information for this data source.  Only the unit and description of the source can be changed this way.

Request
^^^^^^^
Format: *Form encoded*

=================  =================  ==============================================
Field name         Type               Description
=================  =================  ==============================================
``unit``           String             Unit of measure.  May be empty string.
``description``    String             Description of data source.  May be empty string.
=================  =================  ==============================================

Response: Success (200)
^^^^^^^^^^^^^^^^^^^^^^^
Format: *JSON*

Success.

==========  =================  ==============================================
Field name  Type               Description
==========  =================  ==============================================
``result``  String             Contains ``ok`` on success.
==========  =================  ==============================================

Response: Failure (400)
^^^^^^^^^^^^^^^^^^^^^^^
Format: *JSON*

Failure can only happen if the form arguments have incorrect type.

==========  =================  ==============================================
Field name  Type               Description
==========  =================  ==============================================
``result``  String             Contains ``fail`` on failure.
``msg``     String             A short explanation of the error.
==========  =================  ==============================================


``GET /query/``
------------------
Resample the selected data sources and return the result.  The query engine may return results with slightly different first and last times, as well as a different number of points. If ``last`` is omitted, the request is interpreted as a *continuous query* and the requested results and any future results are pushed via a persistent server-sent events (SSE) connection.

=================  =================  ==============================================
Field name         Type               Description
=================  =================  ==============================================
``selectors``      List of strings    Names of data sources to query, with optional overide of reduction and interpolation strategy.  See :ref:`making-query` for more details.
``first``          String             ISO 8601 timestamp of desired first resampling point.
``last``           String (Optional)  ISO 8601 timestamp of desired last resampling point.
``npoints``        Number             Desired number of data points (including first and last point)
=================  =================  ==============================================

Response: Success (200)
^^^^^^^^^^^^^^^^^^^^^^^
Format: *JSON*

Success.

==========  =================  ==============================================
Field name  Type               Description
==========  =================  ==============================================
``times``   List of strings    ISO 8601 timestamps of each resampled point.
``values``  List of lists      List of resampled points.  See :ref:`making-query` for more details.
==========  =================  ==============================================

Response (continuous query): Success (200)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Format: *text/event-stream* containing *JSON*-encoded data

Success.

The ``data`` section of each SSE message contains the following in JSON:

==========  =================  ==============================================
Field name  Type               Description
==========  =================  ==============================================
``time``    String             ISO 8601 timestamps of resampled point.
``value``   List               List of resampled points.  See :ref:`making-query` for more details.
==========  =================  ==============================================

Response: Failure (400)
^^^^^^^^^^^^^^^^^^^^^^^
Format: *JSON*

Failure can happen if the selectors are incorrect, ``first`` is not before ``last``, or ``npoints`` is less than 2.

==========  =================  ==============================================
Field name  Type               Description
==========  =================  ==============================================
``msg``     String             A short explanation of the error.
==========  =================  ==============================================
