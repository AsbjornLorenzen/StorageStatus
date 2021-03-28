from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import sessionmaker, scoped_session
import os

databaseurl = 'sqlite:///' + os.getcwd() + '/storagestatus.db'
engine = create_engine(databaseurl,echo=True)
LocalSession = sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base = declarative_base(engine)
