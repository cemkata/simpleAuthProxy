from flask import Flask, request, render_template, redirect, abort
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required, logout_user
from flask_basicauth import BasicAuth

import os
import sqlite3
import hashlib
from datetime import datetime, timedelta
import json

app = Flask(__name__)

with open('proxy_config.json', 'r') as file:
    data = json.load(file)

db_name = data['authentication_server']['sessions']['users_db']

app.secret_key = data['authentication_server']['sessions']['sessionsSecret']
app.config['BASIC_AUTH_USERNAME'] = data['authentication_server']['auth_username']
app.config['BASIC_AUTH_PASSWORD'] = data['authentication_server']['auth_password']

basic_auth = BasicAuth()
basic_auth.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    pass

@app.route("/")
@basic_auth.required
def home_page():
    if not request.remote_addr.startswith('127.'):
        return ''
    return render_template("index.html",current_user=current_user, welcome_msg=data['authentication_server']['sessions']['customMsg'])

@app.route("/login", methods=['GET','POST'])
@basic_auth.required
def login_page():
    if not request.remote_addr.startswith('127.'):
        abort(404)
    error_message = ""
    if request.method == 'POST':
        if current_user.is_active:
            return redirect("/")
            return 'has logined'
        username = request.form['username']
        password = encryptPass(request.form['password'])
        user_find = execSQL(f"""SELECT `PASSWORD` FROM `users_tbl` WHERE `NAME`='{username}';""")
        if user_find and user_find[0][0]==password:
            user = User()
            user.id = username
            session_duration = datetime.now() + timedelta(days=data['authentication_server']['sessions']['sessionsDuration'])
            login_user(user, duration=session_duration)
            return redirect("/")
            return render_template("index.html", current_user=current_user, welcome_msg=data['authentication_server']['sessions']['customMsg'])
        elif user_find:
            error_message = '\\nWrong password'
        else:
            error_message = "\\nUnknown username"
        return render_template("login.html",error_message=error_message,current_user=current_user, welcome_msg=data['authentication_server']['sessions']['customMsg'])
    return render_template("login.html")

@login_manager.user_loader
def user_loader(username):
    user = User()
    user.id = username
    return user

@app.route('/logout')
@basic_auth.required
def logout_page():
    if not request.remote_addr.startswith('127.'):
        abort(404)
    if current_user.is_active:
        logout_user()
        return redirect("/")
        return 'Logged out'
    else:
        return redirect("/")
        return "you aren't login"

@app.route('/protected')
@login_required  # intumu.com
def protected_page():
    if not request.remote_addr.startswith('127.'):
        abort(404)
    if current_user.is_active:
        #return 'Logged in as: ' + current_user.id + 'Login is_active: True Logged from IP: ' + request.remote_addr
        return ''

def execSQL(sql_query_str):
    try:
        sqliteConnection = sqlite3.connect(db_name)
        cursor = sqliteConnection.cursor()
        cursor.execute(sql_query_str)
        result = cursor.fetchall()
        cursor.close()
        return result

    except sqlite3.Error as error:
        tk.messagebox.showerror("showerror", 'Error occurred - ' + str(error))

    finally:
        if sqliteConnection:
            sqliteConnection.commit()
            sqliteConnection.close()

def encryptPass(clear_txt_pass):
    hash_object = hashlib.sha1(clear_txt_pass.encode())
    return hash_object.hexdigest()

def initDB():
    if not os.path.exists(db_name):
        try:
            sqliteConnection = sqlite3.connect(db_name)
            cursor = sqliteConnection.cursor()
            cursor.executescript(db_creation_script)
        except sqlite3.Error as error:
            tk.messagebox.showerror("showerror", 'Error occurred - ' + str(error))

        finally:
            if sqliteConnection:
                sqliteConnection.commit()
                sqliteConnection.close()

db_creation_script ='''BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "users_tbl" (
	"ID"	INTEGER NOT NULL DEFAULT 101 UNIQUE,
	"NAME"	TEXT NOT NULL,
	"PASSWORD"	TEXT NOT NULL,
	PRIMARY KEY("ID" AUTOINCREMENT)
);
COMMIT;'''

if __name__ == '__main__':
    initDB()
    app.run(host=data['authentication_server']['ip'], port=int(data['authentication_server']['port']), debug=True)
    # In production, run via a WSGI server (gunicorn, waitress, uWSGI)
