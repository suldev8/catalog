#!/usr/bin/python2
from flask import (Flask, render_template, request, redirect, jsonify, abort,
                   url_for, flash, make_response, session as login_session)

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from database_setup import Base, User, Category, Item

import random
import string
import json
import httplib2
import requests

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

engine = create_engine('postgresql+psycopg2://suldev8:1212@localhost/catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog"

# the home route is showing the categoris and latest 10 items


@app.route('/')
def home():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(desc(Item.created)).limit(10)
    if 'username' not in login_session:
        return render_template('home/public_home.html',
                               categories=categories,
                               items=items)
    return render_template('home/private_home.html',
                           categories=categories,
                           items=items)

# generate a state and show the login page


@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# connect google account using OAuth2


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        print("ivalid state")
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        print("invalid secrets")
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

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
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    flash("you are now logged in as %s" % login_session['username'])
    print("Sucessfully logged in!")
    return "Sucessful login"

# User Helper Functions


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
    except NoResultFound:
        return None

# Dissconnect google account- Revoke a current user's token


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
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

# logout user and reset login_session


@app.route('/logout')
def logout():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have sucessfully logged out")
        return redirect(url_for('home'))
    else:
        flash('You already were not logged in')
        return redirect(url_for('home'))

# route to show the items of a specific category


@app.route('/catalog/<string:category_name>/items')
def showCategory(category_name):
    categories = session.query(Category).all()
    items = session.query(Item).filter_by(category_name=category_name).all()
    numberOfItems = session.query(Item).filter_by(
        category_name=category_name).count()
    if 'username' not in login_session:
        return render_template(
            'category/public_category.html',
            categories=categories,
            items=items,
            category_name=category_name,
            numberOfItems=numberOfItems)
    return render_template(
        'category/private_category.html',
        categories=categories,
        items=items,
        category_name=category_name,
        numberOfItems=numberOfItems)

# route to show the item description


@app.route('/catalog/<string:category_name>/<string:item_name>')
def showItem(category_name, item_name):
    item = session.query(Item).filter_by(
        category_name=category_name, name=item_name).one()

    if 'username' not in login_session:
        return render_template('item/public_item.html',
                               item=item,
                               logged=False)

    if login_session['user_id'] != item.user_id:
        return render_template('item/public_item.html', item=item, logged=True)

    return render_template('item/private_item.html', item=item)

# route to add new item to a ctegory


@app.route('/add', methods=['GET', 'POST'])
def addItem():
    if request.method == 'GET':
        if 'username' not in login_session:
            return redirect(url_for('login'))
        elif login_session['user_id'] != editItem.user_id:
            return abort(401)
        categories = session.query(Category).all()
        return render_template('cruds/add_item.html', categories=categories)

    if request.method == 'POST':
        try:
            session.query(Item).filter_by(name=request.form['name']).one()
            flash('Can not add this item, already added')
            return redirect(url_for('home'))
        except NoResultFound:
            newItem = Item(
                name=request.form['name'],
                description=request.form['description'],
                category_name=request.form['category_name'],
                user_id=login_session['user_id']
            )
            session.add(newItem)
            session.commit()
            flash("New item sucessfully added!")
            return redirect(url_for('home'))

# route to be able to edit an item if the user is the owner


@app.route('/catalog/<string:category_name>/<string:item_name>/edit',
           methods=['GET', 'POST'])
def editItem(category_name, item_name):
    editItem = session.query(Item).filter_by(
        category_name=category_name, name=item_name).one()

    if request.method == 'GET':
        if 'username' not in login_session:
            return redirect(url_for('login'))
        elif login_session['user_id'] != editItem.user_id:
            return abort(401)
        categories = session.query(Category).all()
        return render_template('cruds/edit_item.html',
                               item=editItem,
                               categories=categories)

    if request.method == 'POST':
        try:
            session.query(Item).filter_by(name=request.form['name']).one()
            flash('Can not edit this item\'s name, with the same other item')
            return redirect(url_for('home'))
        except NoResultFound:
            if request.form['name']:
                editItem.name = request.form['name']
            if request.form['description']:
                editItem.description = request.form['description']
            if request.form['category_name']:
                editItem.category_name = request.form['category_name']
            session.add(editItem)
            session.commit()
            flash('Item sucessfully edited!')
            return redirect(url_for('home'))

# route to be able to delete an item if the user is the owner


@app.route('/catalog/<string:category_name>/<string:item_name>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    deleteItem = session.query(Item).filter_by(
        category_name=category_name, name=item_name).one()
    if request.method == 'GET':
        if 'username' not in login_session:
            return redirect(url_for('login'))
        elif login_session['user_id'] != deleteItem.user_id:
            return abort(401)
        return render_template('cruds/delete_item.html',
                               category_name=category_name,
                               item_name=item_name)

    if request.method == 'POST':
        session.delete(deleteItem)
        flash('Item sucessfully deleted!')
        return redirect(url_for('home'))

# JSON endpoint that returns all categories data and their related item


@app.route('/catalog.json')
def catalogJson():
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])

# JSON endpoint that returns the items of a specific category


@app.route('/catalog/<string:category_name>.json')
def categoriesJson(category_name):
    items = session.query(Item).filter_by(category_name=category_name).all()
    return jsonify(items=[i.serialize for i in items])

# JSON endpoint that returns a specfic items of a specific category


@app.route('/catalog/<string:category_name>/<item_name>.json')
def itemJson(category_name, item_name):
    item = session.query(Item).filter_by(
        category_name=category_name, name=item_name).one()
    return jsonify(item=item.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
