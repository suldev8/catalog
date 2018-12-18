from flask import (Flask, render_template, request, redirect, jsonify,
    url_for, flash, make_response, session as login_session)

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Category, Item

engine = create_engine('sqlite:///catalog.db?check_same_thread=False')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

@app.route('/')
def home():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(desc(Item.created)).limit(10)
    return render_template('home.html', categories=categories, items=items)

@app.route('/catalog/<string:category_name>/items')
def showCategory(category_name):
    categories = session.query(Category).all()
    items = session.query(Item).filter_by(category_name=category_name).all()
    numberOfItems = session.query(Item).filter_by(category_name=category_name).count()
    return render_template(
        'category.html', 
        categories=categories, 
        items=items, 
        category_name=category_name,
        numberOfItems=numberOfItems)

@app.route('/catalog/<string:category_name>/<string:item_name>')
def showItem(category_name, item_name):
    item = session.query(Item).filter_by(category_name=category_name, name=item_name).one()
    return render_template('item.html', item=item)

@app.route('/add', methods=['GET', 'POST'])
def addItem():
    if request.method == 'GET':
        categories = session.query(Category).all()
        return render_template('addItem.html', categories=categories)

@app.route('/catalog/<string:category_name>/<string:item_name>/edit', methods=['GET', 'POST'])
def editItem(category_name, item_name):
    item = session.query(Item).filter_by(category_name=category_name, name=item_name).one()
    if request.method == 'GET':
        categories = session.query(Category).all()
        return render_template('editItem.html', item=item, categories=categories)
    return category_name + item_name

@app.route('/catalog/<string:category_name>/<string:item_name>/delete', methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    if request.method == 'GET':
        return render_template('deleteItem.html', category_name=category_name, item_name=item_name)
    return category_name + item_name

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)