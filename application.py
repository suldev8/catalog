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
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            category_name=request.form['category_name'],
            user_id=1
        )
        session.add(newItem)
        session.commit()
        flash("New item sucessfully added!")
        return redirect(url_for('home'))

@app.route('/catalog/<string:category_name>/<string:item_name>/edit', methods=['GET', 'POST'])
def editItem(category_name, item_name):
    editItem = session.query(Item).filter_by(category_name=category_name, name=item_name).one()
    if request.method == 'GET':
        categories = session.query(Category).all()
        return render_template('editItem.html', item=editItem, categories=categories)
    if request.method == 'POST':
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

@app.route('/catalog/<string:category_name>/<string:item_name>/delete', methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    if request.method == 'GET':
        return render_template('deleteItem.html', category_name=category_name, item_name=item_name)
    if request.method == 'POST':
        deleteItem = session.query(Item).filter_by(category_name=category_name, name=item_name).one()
        session.delete(deleteItem)
        flash('Item sucessfully deleted!')
        return redirect(url_for('home'))

@app.route('/categories.json')
def categoriesJson():
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])

@app.route('/items.json')
def itemsJson():
    items = session.query(Item).all()
    return jsonify(items=[i.serialize for i in items])

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)