from sqlalchemy import create_engine, Column, Integer, String, \
    DateTime, Float, PickleType, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ln.backend.base import Backend, Blob
from ln.backend.exception import SeriesCreationError, \
    SeriesDoesNotExistError, SeriesTimeOrderError, BadSelectorError
from ln.backend.datatype import parse_datatype
from ln.backend.selector import parse_selector, create_selector
from ln.backend.compat import get_total_seconds

from datetime import datetime
import time
from contextlib import contextmanager

##### SQLAlchemy tables

Base = declarative_base()


class Series(Base):
    __tablename__ = 'series'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    reduction = Column(String)
    interpolation = Column(String)
    unit = Column(String)
    description = Column(String)
    meta = Column(String)

    def __init__(self, name, type, reduction, interpolation, unit,
        description, meta):
        self.name = name
        self.type = type
        self.reduction = reduction
        self.interpolation = interpolation
        self.unit = unit
        self.description = description
        self.meta = meta


class CommonData(object):
    '''Mixin which adds common columns to data tables'''
    id = Column(Integer, primary_key=True)
    name = Column(String)
    sequence = Column(Integer)
    timestamp = Column(DateTime)


class IntValues(CommonData, Base):
    __tablename__ = 'int'
    value = Column(Integer)


class FloatValues(CommonData, Base):
    __tablename__ = 'float'
    value = Column(Float)


class ArrayValues(CommonData, Base):
    __tablename__ = 'array'
    value = Column(PickleType)


class BlobValues(CommonData, Base):
    __tablename__ = 'blob'
    value = Column(LargeBinary)


#####

class SQLBlob(Blob):
    '''A blob stored in the SQL database'''

    def __init__(self, index, mimetype, series_name, backend):
        super(SQLBlob, self).__init__(index, mimetype)
        self.series_name = series_name
        self._backend = backend

    def get_bytes(self):
        session = self._backend._sessionmaker()
        return session.query(BlobValues.value).filter_by(name=self.series_name,
            sequence=self.index).first().value




class SQLBackend(Backend):
    '''Backend based on SQLAlchemy'''

    def __init__(self, url):
        '''Connect to an SQL-based Natural Log storage backend.

        :param url: SQLAlchemy-format url
        '''
        super(Backend, self).__init__()
        self._engine = create_engine(url)
        Base.metadata.create_all(self._engine)
        self._sessionmaker = sessionmaker(bind=self._engine)

    @contextmanager
    def session_scope(self):
        '''Provide a transactional scope around a series of operations.'''
        session = self._sessionmaker()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def get_series_list(self):
        with self.session_scope() as session:
            return [row.name for row in session.query(Series.name)]

    def create_series(self, name, type, reduction, interpolation, unit,
            description, metadata):

        # Raises exception if datatype is invalid
        parse_datatype(type)

        with self.session_scope() as session:
            if session.query(Series).filter_by(name=name).count() != 0:
                raise SeriesCreationError('Series %s already exists.'
                    % name)

            series = Series(name=name, type=type, reduction=reduction,
                interpolation=interpolation, unit=unit, description=description,
                meta=metadata)
            session.add(series)

    def get_config(self, name):
        with self.session_scope() as session:
            series = session.query(Series).filter_by(name=name).first()
            if series is None:
                return None
            else:
                config = dict([(k, getattr(series, k)) for k in
                    ('name', 'type', 'reduction',
                    'interpolation', 'unit', 'description')])
                # "metadata" is used by SQLAlchemy, so the field is named "meta"
                config['metadata'] = series.meta
                return config

    def update_config(self, name, unit=None, description=None, metadata=None):
        with self.session_scope() as session:
            series = session.query(Series).filter_by(name=name).first()

            if series is None:
                raise SeriesDoesNotExistError('Series %s does not exist.' % name)

            if unit is not None:
                series.unit = unit
            if description is not None:
                series.description = description
            if metadata is not None:
                series.meta = metadata

    def _pick_table(self, datatype):
        # select table based on type
        if datatype.is_int_scalar():
            return IntValues
        elif datatype.is_float_scalar():
            return FloatValues
        elif datatype.is_array():
            return ArrayValues
        elif datatype.is_blob():
            return BlobValues

    def add_data(self, name, time, value):
        with self.session_scope() as session:
            config = session.query(Series.name, Series.type).filter_by(name=name).first()

            if config is None:
                raise SeriesDoesNotExistError('Series %s does not exist.' % name)

            datatype = parse_datatype(config.type)
            value = datatype.coerce(value)
            table = self._pick_table(datatype)

            # get last entry for this series (if exists)
            last_entry = session.query(table.timestamp, table.sequence) \
                .filter_by(name=name).order_by(table.timestamp.desc()).first()

            # compute new sequence number
            if last_entry is None:
                sequence = 0
            else:
                if last_entry.timestamp > time:
                    raise SeriesTimeOrderError('New data point is chronologically before last point in series')
                sequence = last_entry.sequence + 1

            # create new entry
            entry = table(name=name, sequence=sequence, timestamp=time,
                value=value)
            session.add(entry)
            return sequence

    def get_data(self, name, offset=None, limit=None):
        with self.session_scope() as session:
            config = session.query(Series.name, Series.type).filter_by(name=name).first()

            if config is None:
                raise SeriesDoesNotExistError('Series %s does not exist.' % name)

            datatype = parse_datatype(config.type)
            table = self._pick_table(datatype)

            # Select appropriate columns from table
            if datatype.is_blob():
                query = session.query(table.sequence, table.timestamp)\
                    .filter_by(name=name)
            else:
                query = session.query(table.sequence, table.timestamp, table.value)\
                    .filter_by(name=name)

            # Decide how many entries to fetch
            if offset == None:  # get last entry
                row = query.order_by(table.sequence.desc()).first()

                if row is None:
                    return [], [], None  # No entry to return
                elif datatype.is_blob():
                    value = SQLBlob(index=row.sequence, mimetype=datatype.mimetype,
                        series_name=name, backend=self)
                else:
                    value = datatype.convert_to_jsonable(row.value)

                return [row.timestamp], [value], None
            else:
                query = query.order_by(table.sequence)

                # Apply limits and decide what the next sequence number is, if any
                if limit is None:
                    rows = query[offset:]
                    next_offset = None
                else:
                    rows = query[offset:offset + limit + 1]
                    if len(rows) > limit:
                        next_offset = rows[-1].sequence
                    else:
                        next_offset = None
                    rows = rows[:limit]

                times = []
                values = []

                for row in rows:
                    times.append(row.timestamp)
                    if datatype.is_blob():
                        value = SQLBlob(index=row.sequence,
                            mimetype=datatype.mimetype,
                            series_name=name, backend=self)
                    else:
                        value = datatype.convert_to_jsonable(row.value)
                    values.append(value)

                return times, values, next_offset

    def _get_resampled_series(self, selectors, bin_lower, bin_upper, bin_center):
        '''Return the resampled points for the given selectors using the list
        of datetimes provided in bin_lower and bin_upper.

        :param selectors: list of Selector objects
        :param bin_lower: list of datetimes representing lower bin boundaries
        :param bin_upper: list of datetimes representing upper bin boundaries
        :param bin_center: list of datetimes representing the center of each bin

        Returns: List of lists of resampled points.  Top level list is indexed
        by selector, and each sublist is the list of points in the order
        of the bin boundaries.
        '''
        with self.session_scope() as session:
            resampled_series = []
            for selector in selectors:
                table = self._pick_table(selector.datatype)
                raw_values = session.query(table.timestamp, table.value) \
                    .order_by(table.sequence).filter(
                        table.timestamp >= bin_lower[0],
                        table.timestamp < bin_upper[-1]
                    ).all()

                groups = [[] for i in range(len(bin_lower))]
                current_group = 0
                for row in raw_values:
                    while row.timestamp >= bin_upper[current_group]:
                        current_group += 1
                    groups[current_group].append((row.timestamp, row.value))

                resampled_points = [selector.datatype.convert_to_jsonable(value)
                    for value in selector.apply_strategies(bin_center, groups)]
                resampled_series.append(resampled_points)
            return resampled_series

    def _query(self, selectors, first, last, npoints):
        '''Common core of query implementation shared between ``query``
        and ``query_continuous``.

        Returns: list of timestamps, list of resampled series (each a list of
            resampled points), list of Selector objects,
            timedelta between timestamps
        '''

        # Parse selectors
        selector_objs = []
        for selector in selectors:
            name, reduce_strategy, interp_strategy = parse_selector(selector)
            config = self.get_config(name)
            if config is None:
                raise BadSelectorError('Unknown series name "%s"' % name)

            selector_obj = create_selector(series_config=config,
                reduction=reduce_strategy, interpolation=interp_strategy)
            selector_objs.append(selector_obj)

        # Compute bin boundaries
        bin_half_delta = (last - first) / ((npoints - 1) * 2)
        bin_boundaries = [first + bin_half_delta * (2 * i - 1)
            for i in range(npoints + 1)]
        bin_centers = [first + bin_half_delta * (2 * i)
            for i in range(npoints)]

        # Collect and resample points for each series
        resampled_series = self._get_resampled_series(selector_objs,
            bin_boundaries[:-1], bin_boundaries[1:], bin_centers)

        return bin_centers, resampled_series, selector_objs, 2 * bin_half_delta

    def query(self, selectors, first, last, npoints):
        times, values, _, _ = self._query(selectors, first, last, npoints)
        return times, values

    def _generate_values(self, selectors, next_t, delta_t):
        '''Generate new query results every delta_t interval.'''

        while True:
            next_query_time = next_t + delta_t / 2
            sleep_time = get_total_seconds(next_query_time - datetime.now())
            if sleep_time > 0:
                time.sleep(sleep_time)

            bin_lower = [next_t - delta_t / 2]
            bin_upper = [next_t + delta_t / 2]
            bin_center = [next_t]

            resampled_series = self._get_resampled_series(selectors,
                bin_lower, bin_upper, bin_center)
            yield bin_center, resampled_series

            next_t = next_t + delta_t

    def query_continuous(self, selectors, first, npoints):
        last = datetime.now()
        times, values, selector_objs, delta_t = self._query(selectors, first,
            last, npoints)
        gen = self._generate_values(selector_objs, last + delta_t, delta_t)

        return times, values, gen
