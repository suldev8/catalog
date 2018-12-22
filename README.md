# Catalog

Catalog is a web application that provides a list of items within a variety of categories as well as provides Google's OAuth 2.0 authentication system for user login. Registered users will have the ability to post, edit and delete their own items.

## Prerequisites
This web app was built using Python 2.7.12

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install all the requirements. In the root directory of the repository, run this command to install all the required packages from the requirements.txt file.

```bash
cd catalog
pip install -r requirements.txt
```

## Usage
For the first time running before we need to set up the database and put some data into it by running the seeder file.
```bash
python seeder.py
``` 
Then, to run the web server run this command. It will be running on [http://localhost:5000](http://localhost:5000)
```bash
python application.py
```
### JSON enpoints
These endpoints to get data from the database as JSON. 

Endpoint to get all the categories and their items.
 
> **[GET]** /catalog.json

Endpoint to get items of a specific category.

> **[GET]** /categories/{category_name}.json
 
Endpoint to get all items in the database.

>**[GET]** /items.json