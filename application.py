from flask import (Flask, render_template, request, redirect, jsonify,
    url_for, flash, make_response, session as login_session)

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Category, Item

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello World'

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)