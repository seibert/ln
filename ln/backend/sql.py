from sqlalchemy import create_engine, Column, Integer, String, \
    DateTime, Float, PickleType, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ln.backend.base import Backend
from ln.backend.exception import SeriesCreationError, SeriesUpdateError
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

TYPE_MAPPING = {
    'int8' : 'int',
    'int16': 'int',
    'int32': 'int',
    'int64': 'int',
    'float32':'real',
    'float64':'real',
}


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
            raise SeriesUpdateError('Series %s does not exist.' % name)

        if unit is not None:
            series.unit = unit
        if description is not None:
            series.description = description
        if metadata is not None:
            series.meta = metadata

        session.commit()
