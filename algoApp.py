from flask import Flask, render_template
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'kwokhung'
app.config['MYSQL_PASSWORD'] = 'chu9999'
app.config['MYSQL_DB'] = 'algotrade'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/users')
def users():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM users")

    if result > 0:
        users = cur.fetchall()

        return render_template('users.html', users=users)
    else:
        msg = 'No user found'

        return render_template('users.html', msg=msg)

    cur.close()


if __name__ == '__main__':
    app.run(debug=True)
