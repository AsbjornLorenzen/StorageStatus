from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.types import Date, PickleType
from sqlalchemy.ext.mutable import Mutable
from sqlalchconn import Base
from datetime import date
import random

class component_lot(Base):
    __tablename__ = 'Storagedata'
    lotnr = Column(String,primary_key=True)
    storagetype = Column(String)
    articlenr = Column(String)
    amountinstore = Column(Integer)

    def __init__(self,dataset):
        self.storagetype = dataset.get('storagetype')
        self.articlenr = dataset.get('articlenr')
        self.amountinstore = dataset.get('amountinstore')
        self.lotnr = dataset.get('lotnr')

    def __str__(self):
        return self.lotnr+'-'+self.storagetype

class device(Base):
    __tablename__ = 'devices'
    devicenr = Column(Integer, primary_key = True)
    contents = Column(PickleType)

    def __init__(self,data,devnr):
        self.devicenr = devnr
        self.contents = data

class backupdevice(Base):
    __tablename__ = 'backupdevices'
    devicenr = Column(Integer, primary_key = True)
    contents = Column(PickleType)

    def __init__(self,olddevice):
        self.devicenr = olddevice.devicenr
        self.contents = olddevice.contents