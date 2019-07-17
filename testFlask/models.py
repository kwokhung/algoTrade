# 建立資料表欄位
from testFlask.main import db


class Todo(db.Model):
    # __table__name = 'user_table'，若不寫則看 class name
    # 設定 primary_key
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(80))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return '<Todo %r>' % self.content


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))

    todos = db.relationship(
        'Todo',
        backref='user',  # ref 可以讓我們使用 Todo.user 進行對 User 操作
        lazy='dynamic'  # 有使用才載入，提昇效能
    )

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<User %r>' % self.name


class Post(db.Model):
    # __table__name = 'user_table'，若不寫則看小寫 class name
    # 設定 primary_key
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    content = db.Column(db.String(80))

    def __init__(self, title, content):
        self.title = title
        self.content = content

    def __repr__(self):
        return '<Post %r>' % self.content


class Tag(db.Model):
    # __table__name = 'user_table'，若不寫則看 class name
    # 設定 primary_key
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))

    tags = db.Table('post_tags',
                    db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
                    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
                    )

    def __init__(self, title):
        self.title = title

    def __repr__(self):
        return '<Tag %r>' % self.title
