#!/usr/bin/env python
#
# lotsofitems.py -- Run this script to create a few sample collections and items
#
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Collection, Base, CollectionItem, User

engine = create_engine('sqlite:///ecommerce.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Robo Jeweler", email="tinnyTim@udacity.com",
             picture='https://lh4.googleusercontent.com/-4C4VRukGkfo/'
             'AAAAAAAAAAI/AAAAAAAAAFg/HXs8ESdx8pY/photo.jpg')
session.add(User1)
session.commit()

# Items for the Coral collection
collection1 = Collection(user_id=1, name="Coral collection", t_pic="coral.jpg")

session.add(collection1)
session.commit()

collectionItem2 = CollectionItem(user_id=1, name="Coral necklace",
                                 description="An elegant scarlet coral"
                                 "necklace, ideal to compliment a summer look",
                                 price="$57.50", category="Necklace",
                                 collection=collection1)

session.add(collectionItem2)
session.commit()


collectionItem1 = CollectionItem(user_id=1, name="Coral Bracelet",
                                 description="A statement piece to decorate"
                                 "your wrist with the intensity of coral",
                                 price="$32.99", category="Bracelet",
                                 collection=collection1)

session.add(collectionItem1)
session.commit()

collectionItem2 = CollectionItem(user_id=1, name="Coral earring",
                                 description="Nice earrings to kick ass this"
                                 "summer", price="$25.50",
                                 category="Earrings", collection=collection1)

session.add(collectionItem2)
session.commit()

collectionItem3 = CollectionItem(user_id=1, name="Coral Necklace long",
                                 description="A longer necklace to show that"
                                 "you can rock whatever you want",
                                 price="$83.99", category="Necklace",
                                 collection=collection1)

session.add(collectionItem3)
session.commit()


# Items for the stone collection
collection2 = Collection(user_id=1, name="Stone collection", t_pic="stone.jpg")

session.add(collection2)
session.commit()


collectionItem2 = CollectionItem(user_id=1, name="Stone necklace",
                                 description="A badass necklace taht shouts"
                                 "badassery", price="$57.50",
                                 category="Necklace", collection=collection2)

session.add(collectionItem2)
session.commit()


collectionItem1 = CollectionItem(user_id=1, name="Stone Bracelet",
                                 description="A bracelect crafted out of onyx,"
                                 "adds strenght +3 and mana +1",
                                 price="$32.99", category="Bracelet",
                                 collection=collection2)

session.add(collectionItem1)
session.commit()

collectionItem2 = CollectionItem(user_id=1, name="Stone earring",
                                 description="These earrings are artfully"
                                 "crafted to accentuate your visage",
                                 price="$25.50", category="Earring",
                                 collection=collection2)

session.add(collectionItem2)
session.commit()

collectionItem3 = CollectionItem(user_id=1, name="Stone Necklace long",
                                 description="Following the teachings of"
                                 "master Muten, this long necklace"
                                 "will strenghten your core and leg muscles",
                                 price="$83.99", category="Necklace",
                                 collection=collection2)

session.add(collectionItem3)
session.commit()

print "added Collections and items!"
