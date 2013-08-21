.. ln documentation master file, created by
   sphinx-quickstart on Sat Jul 13 14:34:16 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Natural Log's documentation!
=======================================

Natural Log (ln for short) is a time series database with a REST API.  The database records time-varying scalars, arrays, and generic binary data at irregularly-spaced intervals, and supports time-oriented queries on that data.  It is primarly intended for logging numeric data, rather than string messages like syslog.

.. warning:: Natural Log is currently practicing "Documentation Driven Development," so none of the code exists to do any of this yet.

The key feature of Natural Log is its support for *resampling queries*.  In such queries, the server takes the raw, irregularly-spaced time series and returns a new time series with equally spaced intervals of (approximately) the requested size.  This can be used to reduce a time series sampled very finely to one sampled much more coarsely without having to transfer a large amount of data to a plotting client.  Moreover, two time series *(t,x)* and *(t,y)* can be more easily joined to create an *(x,y)* series if the time series first can be resampled to the same points in time.

Different resampling strategies are required for different applications, so Natural Log allows both the reduction (used to combine raw points) and interpolation (used between raw points) strategies to be selected as part of the query.  See :ref:`reduction` and :ref:`interpolation` for more information.


Contents
--------

.. toctree::
   :maxdepth: 1

   install
   data
   record
   query
   rest


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

