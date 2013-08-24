from sqlalchemy import create_engine, Column, Integer, String, \
    DateTime, Float, PickleType, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ln.backend.base import Backend, Blob
from ln.backend.exception import SeriesCreationError, \
    SeriesDoesNotExistError, SeriesTimeOrderError
from ln.backend.datatype import parse_datatype

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
        self._engine = create_engine(url)
        Base.metadata.create_all(self._engine)
        self._sessionmaker = sessionmaker(bind=self._engine)

    def get_series_list(self):
        session = self._sessionmaker()
        return [row.name for row in session.query(Series.name)]

    def create_series(self, name, type, reduction, interpolation, unit,
            description, metadata):

        # Raises exception if datatype is invalid
        parse_datatype(type)

        session = self._sessionmaker()

        if session.query(Series).filter_by(name=name).count() != 0:
            raise SeriesCreationError('Series %s already exists.'
                % name)

        series = Series(name=name, type=type, reduction=reduction,
            interpolation=interpolation, unit=unit, description=description,
            meta=metadata)
        session.add(series)
        session.commit()

    def get_config(self, name):
        session = self._sessionmaker()
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
        session = self._sessionmaker()
        series = session.query(Series).filter_by(name=name).first()

        if series is None:
            raise SeriesDoesNotExistError('Series %s does not exist.' % name)

        if unit is not None:
            series.unit = unit
        if description is not None:
            series.description = description
        if metadata is not None:
            series.meta = metadata

        session.commit()

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
        session = self._sessionmaker()
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
        session.commit()
        return sequence

    def get_data(self, name, offset=None, limit=None):
        session = self._sessionmaker()
        config = session.query(Series.name, Series.type).filter_by(name=name).first()

        if config is None:
            raise SeriesDoesNotExistError('Series %s does not exist.' % name)

        datatype = parse_datatype(config.type)
        table = self._pick_table(datatype)

        if datatype.is_blob():
            query = session.query(table.sequence, table.timestamp)\
                .filter_by(name=name)
        else:
            query = session.query(table.sequence, table.timestamp, table.value)\
                .filter_by(name=name)

        if offset == None:  # get last entry
            row = query.order_by(table.sequence.desc()).first()
            if datatype.is_blob():
                value = SQLBlob(index=row.sequence, mimetype=datatype.mimetype,
                    series_name=name, backend=self)
            else:
                value = row.value
            return [row.timestamp], [value], None
        else:
            query = query.order_by(table.sequence)
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
                    value = row.value
                values.append(value)

            return times, values, next_offset
