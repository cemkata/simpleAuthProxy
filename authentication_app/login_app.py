from flask import Flask, request, render_template, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required, logout_user
import os

import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
import json

os.chdir("..")

app = Flask(__name__)

with open('config.json', 'r') as file:
    data = json.load(file)

app.secret_key = data['sessionsSecret']
db_name = data['users_db']
session_in_days = data['sessionsDuration']

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    pass

@app.route("/")
def home_page():
    return render_template("index.html",current_user=current_user)

@app.route("/login", methods=['GET','POST'])
def login_page():
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
            session_duration = datetime.now() + timedelta(days=session_in_days)
            login_user(user, duration=session_duration)
            return redirect("/")
            return render_template("index.html", current_user=current_user)
        elif user_find:
            error_message = '\\nWrong password'
        else:
            error_message = "\\nUnknown username"
        return render_template("login.html",error_message=error_message,current_user=current_user)
    return render_template("login.html")
    
@login_manager.user_loader  
def user_loader(username):  
    user = User()  
    user.id = username
    return user 
    
@app.route('/logout')  
def logout_page():  
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
    if current_user.is_active:  
        return 'Logged in as: ' + current_user.id + 'Login is_active:True'

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
    app.run(debug=False, port=data['destinationPortAuth'], host=data['destinationIPAuth'])
