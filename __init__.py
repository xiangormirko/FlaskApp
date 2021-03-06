from flask import Flask, render_template, request, g
from flask import redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Collection, CollectionItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from db_helper import getUserID, getUserInfo, createUser
from functools import wraps
app = Flask(__name__)

CLIENT_ID = json.loads(
    open('/var/www/FlaskApp/FlaskApp/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Bijoux Shop Application"


# Connect to Database and create database session
engine = create_engine('postgresql://mirko:holasenor@localhost/ecommercepsql')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# Log in with facebook oauth
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('/var/www/FlaskApp/FlaskApp/fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('/var/www/FlaskApp/FlaskApp/fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.2/me"
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.2/me?%s' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


# revoke authorization from facebook
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions' % (facebook_id+access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


# login with google oauth
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/FlaskApp/FlaskApp/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id
    login_session['credentials'] = credentials.to_json()

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Collection Information

# displays items in a collection by providing collection id
@app.route('/collection/<int:collection_id>/items/JSON')
def collectionItemJSON(collection_id):
    collection = session.query(Collection).filter_by(id=collection_id).one()
    items = session.query(CollectionItem).filter_by(
        collection_id=collection_id).all()
    return jsonify(CollectionItems=[i.serialize for i in items])


# displays information on a specific item by providing both collection and item id
@app.route('/collection/<int:collection_id>/items/<int:item_id>/JSON')
def ItemJSON(collection_id, item_id):
    Collection_Item = session.query(CollectionItem).filter_by(id=item_id).one()
    return jsonify(Collection_Item=Collection_Item.serialize)


# displays all collections
@app.route('/collection/JSON')
def collectionsJSON():
    collections = session.query(Collection).all()
    return jsonify(collections=[c.serialize for c in collections])


# displays all users
@app.route('/users/JSON')
def usersJSON():
    users = session.query(User).all()
    return jsonify(users=[u.serialize for u in users])


# Show all collections
@app.route('/')
@app.route('/collection/')
def showCollections():
    collections = session.query(Collection).order_by(asc(Collection.name))
    if 'username' not in login_session:
        return render_template('publicCollections.html', collections=collections)
    else:
        return render_template('collections.html', collections=collections)

# Create a new collection


@app.route('/collection/new/', methods=['GET', 'POST'])
def newCollection():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCollection = Collection(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCollection)
        flash('New Collection %s Successfully Created' % newCollection.name)
        session.commit()
        return redirect(url_for('showCollections'))
    else:
        return render_template('newCollection.html')

# Edit a collection


@app.route('/collection/<int:collection_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCollection(collection_id):
    editedCollection = session.query(Collection).filter_by(id=collection_id).one()
    if editedCollection.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this collection. Please create your own collection in order to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedCollection.name = request.form['name']
            flash('Collection Successfully Edited %s' % editedCollection.name)
            return redirect(url_for('showCollections'))
    else:
        return render_template('editCollection.html', collection=editedCollection)


# Delete a collection
@app.route('/collection/<int:collection_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCollection(collection_id):
    collectionToDelete = session.query(Collection).filter_by(id=collection_id).one()
    if collectionToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this collection. Please create your own collection in order to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(collectionToDelete)
        flash('%s Successfully Deleted' % collectionToDelete.name)
        session.commit()
        return redirect(url_for('showCollections', collection_id=collection_id))
    else:
        return render_template('deleteCollection.html', collection=collectionToDelete)


# Show a collection and the respective items
@app.route('/collection/<int:collection_id>/')
@app.route('/collection/<int:collection_id>/items/')
def showItems(collection_id):
    collection = session.query(Collection).filter_by(id=collection_id).one()
    creator = getUserInfo(collection.user_id)
    items = session.query(CollectionItem).filter_by(
        collection_id=collection_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicitems.html', items=items, collection=collection, creator=creator)
    else:
        return render_template('items.html', items=items, collection=collection, creator=creator)


# Create a new collection item
@app.route('/collection/<int:collection_id>/items/new/', methods=['GET', 'POST'])
@login_required
def newCollectionItem(collection_id):
    collection = session.query(Collection).filter_by(id=collection_id).one()
    if login_session['user_id'] != collection.user_id:
        return "<script>function myFunction() {alert('You are not authorized to add items to this collection. Please create your own collection in order to add items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        newItem = CollectionItem(name=request.form['name'], description=request.form['description'], price=request.form[
                               'price'], category=request.form['category'], collection_id=collection_id, user_id=collection.user_id)
        session.add(newItem)
        session.commit()
        flash('New %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showItems', collection_id=collection_id))
    else:
        return render_template('newCollectionItem.html', collection_id=collection_id)


# Edit a collection item
@app.route('/collection/<int:collection_id>/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def editCollectionItem(collection_id, item_id):
    editedItem = session.query(CollectionItem).filter_by(id=item_id).one()
    collection = session.query(Collection).filter_by(id=collection_id).one()
    if login_session['user_id'] != collection.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit items in this collection. Please create your own collection in order to edit items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['category']:
            editedItem.category = request.form['category']
        session.add(editedItem)
        session.commit()
        flash('Collection Item Successfully Edited')
        return redirect(url_for('showItems', collection_id=collection_id))
    else:
        return render_template('editCollectionItem.html', collection_id=collection_id, item_id=item_id, item=editedItem)


# Delete a collection item
@app.route('/collection/<int:collection_id>/items/<int:item_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteCollectionItem(collection_id, item_id):
    collection = session.query(Collection).filter_by(id=collection_id).one()
    itemToDelete = session.query(CollectionItem).filter_by(id=item_id).one()
    if login_session['user_id'] != collection.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete items in this collection. Please create your own collection in order to delete items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Collection Item Successfully Deleted')
        return redirect(url_for('showItems', collection_id=collection_id))
    else:
        return render_template('deleteCollectionItem.html', item=itemToDelete)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()

        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCollections'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCollections'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
