from sqlalchemy.orm import (
    scoped_session, relationship,
    sessionmaker
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *
import datetime
import os

basedir = os.getcwd()
engine = create_engine(f"sqlite:///{basedir}/dev.db")
session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)
Base = declarative_base(bind=engine)
# Note class
class Todo(Base):
    __tablename__ = 'todo'
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    description = Column(Text)
    path = Column(String(1000),nullable=True)
    time = Column(DateTime, default=datetime.datetime.utcnow)
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(100))
    user_id = Column(String(100))
    stripe_sessionid = Column(String(100),nullable=True)


    