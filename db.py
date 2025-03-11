from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from appfinal import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'  # Use your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Avoid overhead

db = SQLAlchemy(app)
