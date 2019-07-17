from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'algotrade'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://algotrade:12345678@127.0.0.1:3306/algotrade'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)
