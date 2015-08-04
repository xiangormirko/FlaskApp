#!/usr/bin/env python
#
# database_setup.py -- Run this script create a sqlite database according to the specs below
#

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import sqlalchemy_utils
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'email': self.email,
            'picture': self.picture,
        }

    @hybrid_property
    def getUserInfo(self):
        userInfo = {'id': self.id, 'name': self.name, 'email': self.email, 'picture': self.picture}
        return userInfo


class Collection(Base):
    __tablename__ = 'collection'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    t_pic = Column(String(250))
    user = relationship(User)
    collection_items = relationship("CollectionItem", cascade="all, delete-orphan")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class CollectionItem(Base):
    __tablename__ = 'collection_item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    price = Column(String(8))
    picture = Column(String(250))
    category = Column(String(250))
    collection_id = Column(Integer, ForeignKey('collection.id'))
    collection = relationship(Collection)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,
            'category': self.category,
            'picture': self.picture,
        }

# uncomment the following lines if you wish to recreate the database at file execution
# sqlalchemy_utils.functions.database_exists('sqlite:///ecommerce.db'):
# sqlalchemy_utils.functions.drop_database('sqlite:///ecommerce.db')
# print "An older database has been dropped"

engine = create_engine('postgresql://mirko:holasenor@localhost/ecommercepsql')

Base.metadata.create_all(engine)
