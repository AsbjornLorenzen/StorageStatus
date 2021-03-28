from flask import Flask, render_template, url_for, request, redirect, _app_ctx_stack
#from models import workout
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime

databaseurl = 'sqlite:///storagestatus.db'
engine = create_engine(databaseurl,echo=True)
LocalSession = sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base = declarative_base(engine)
app = Flask(__name__)
app.session = scoped_session(LocalSession,_app_ctx_stack.__ident_func__)
