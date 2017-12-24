'''

models.py: models for a local singularity registry

Copyright (C) 2017 The Board of Trustees of the Leland Stanford Junior
University.
Copyright (C) 2017 Vanessa Sochat.

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''

from sqlalchemy import (
    Column, 
    DateTime,
    Integer, 
    String, 
    Text,
    ForeignKey,
    func
)

from sregistry.logger import bot
from sregistry.defaults import SREGISTRY_DATABASE
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship, backref
from uuid import uuid4

from sqlalchemy.ext.declarative import declarative_base

 
Base = declarative_base()

  
class Collection(Base):
    '''A participant in a local assessment. id must be unique. If a token is
       revoked or finished, it will end with `_revoked` or `_finished`. A
       user generated without a token will have value of None
    '''
    __tablename__ = 'collection'
    id = Column(Integer, primary_key=True)
    name = Column(String(150))
    token = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    containers = relationship('Container',
                              lazy='select',
                              cascade='delete,all',
                              backref=backref('collection', lazy='joined'))

    def __init__(self, name=None, token=None):
        self.name = name
        if token is None:
            token = str(uuid4())
        self.token = token

    def __repr__(self):
        return '<Collection %r>' % (self.name)

    def url(self):
        '''return the collection url'''
        return "file://"        


class Container(Base):
    '''a container belongs to a collection

    Parameters
    ==========
    created_at: the creation date of the image / container
    metrics: typically the inspection of the image. If not possible, then the
             basic name (uri) derived from the user is used.
    tag: the image tag
    image: the path to the image on the filesystem (can be Null)
    url: the url where the imate was ultimately retrieved, call be Null
    client: the client backend associated with the image, the type(client)
    version: a version string associated with the image
    :collection_id: the id of the colletion to which the image belongs.

    We index / filter containers based on the full uri, which is assembled 
               from the <collection>/<namespace>:<tag>@<version>, then stored
               as a variable, and maintained separately for easier query. We also
               maintain separate indices for the storage location, meaning that
               the same image could theoretically come from two different locations,
               and thus be represented twice (although unlikely). This future
               behavior might change.
    '''
    __tablename__ = 'container'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    metrics = Column(Text, nullable=False)
    name = Column(String(250), nullable=False)
    tag = Column(String(250), nullable=False)
    image = Column(String(250), nullable=True)
    url = Column(String(500), nullable=True)
    client = Column(String(500), nullable=False)
    version = Column(String(250), nullable=True)
    collection_id = Column(Integer, 
                           ForeignKey('collection.id'),
                           nullable=False)

    def uri(self):
        return self.name


def init_db(self, db_path):
    '''initialize the database, with the default database path or custom of

       the format sqlite:////scif/data/expfactory.db

    #TODO: when a user creates the client, initialize this db
    the database should use the .singularity cache folder to cache
    layers and images, and .singularity/sregistry.db as a database (with userid)
    '''

    # Database Setup, use default if uri not provided
    self.database = 'sqlite:///%s' % db_path

    bot.info("Database located at %s" % self.database)
    self.engine = create_engine(self.database, convert_unicode=True)
    self.session = scoped_session(sessionmaker(autocommit=False,
                                               autoflush=False,
                                               bind=self.engine))
    
    Base.query = self.session.query_property()

    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    Base.metadata.create_all(bind=self.engine)
    self.Base = Base
