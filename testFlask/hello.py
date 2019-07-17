# 文件名hello.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'algotrade'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://algotrade:12345678@127.0.0.1:3306/algotrade'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    name = db.Column(db.String(16), nullable=False, server_default='', unique=True)

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32), nullable=False, unique=True, server_default='', index=True)
    role_id = db.Column(db.Integer, nullable=False, server_default='0')

    def __repr__(self):
        return '<User %r, Role id %r>'.format(self.username, self.role_id)
