from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Collection, Base, CollectionItem, User
from flask import session as login_session

# Connect to Database and create database session
engine = create_engine('postgresql://mirko:holasenor@localhost/ecommercepsql')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# DB helpwer functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None
