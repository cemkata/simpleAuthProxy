#!/usr/bin/env python3

#https://github.com/peterbrittain/asciimatics/blob/master/samples/contact_list.py

from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget, PopUpDialog
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication

import sys
import os
import sqlite3
import hashlib
import json

os.chdir("..")

db_name = 'users_db'

db_creation_script ='''BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "users_tbl" (
	"ID"	INTEGER NOT NULL DEFAULT 101 UNIQUE,
	"NAME"	TEXT NOT NULL,
	"PASSWORD"	TEXT NOT NULL,
	PRIMARY KEY("ID" AUTOINCREMENT)
);
COMMIT;'''

with open('config.json', 'r') as file:
    data = json.load(file)

db_name = data['users_db']


def encryptPass(clear_txt_pass):
    hash_object = hashlib.sha1(clear_txt_pass.encode())
    return hash_object.hexdigest()

class UsertModel():
    def __init__(self):
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

        self._db = sqlite3.connect(db_name)
        self._db.row_factory = sqlite3.Row
        self._db.commit()

        # Current contact when editing.
        self.current_id = None

    def add(self, data):
        result = self._db.cursor().execute(f"""SELECT COUNT(`NAME`) FROM `users_tbl` WHERE `NAME`='{data['name']}';""").fetchone()
        if result[0] != 0:
            return -3
        pbHash = encryptPass(data['password'])
        self._db.cursor().execute(f"""INSERT INTO `users_tbl` (`NAME`, `PASSWORD`) VALUES('{data['name']}', '{pbHash}')""")
        self._db.commit()
        return 0

    def get_summary(self):
        return self._db.cursor().execute("""SELECT `NAME`, `ID` from `users_tbl`;""").fetchall()

    def get_user(self, data):
        return self._db.cursor().execute(f"""SELECT `NAME`, `ID` from `users_tbl` WHERE `ID`='{data['name']}';""").fetchone()

    def get_current_user(self):
        if self.current_id is None:
            return {"name": "", "password": "", "repassword": ""}
        else:
            return self.get_user({"name": self.current_id})

    def update_current_user(self, data):
        if len(data['name']) == 0:
            return -1
        if data['password'] != data['repassword']:
            return -2
        if self.current_id is None:
           return self.add(data)
        else:
            pbHash = encryptPass(data['password'])
            self._db.cursor().execute(f"""UPDATE `users_tbl` SET `PASSWORD`='{pbHash}' WHERE `NAME`='{data['name']}';""")
            self._db.commit()
        return 0
    def delete_user(self, data):
        self._db.cursor().execute(f"""DELETE FROM `users_tbl` WHERE `ID`='{data}';""")
        self._db.commit()


class ListView(Frame):
    def __init__(self, screen, model):
        super(ListView, self).__init__(screen,
                                       screen.height * 2 // 3,
                                       screen.width * 2 // 3,
                                       on_load=self._reload_list,
                                       hover_focus=True,
                                       can_scroll=False,
                                       title="Users List")
        # Save off the model that accesses the contacts database.
        self._model = model

        # Create the form for displaying the list of contacts.
        self._list_view = ListBox(
            Widget.FILL_FRAME,
            model.get_summary(),
            name="users",
            add_scroll_bar=True,
            on_change=self._on_pick,
            on_select=self._edit)
        self._edit_button = Button("Edit", self._edit)
        self._delete_button = Button("Delete", self._delete)
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._list_view)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Add", self._add), 0)
        layout2.add_widget(self._edit_button, 1)
        layout2.add_widget(self._delete_button, 2)
        layout2.add_widget(Button("Quit", self._quit), 3)
        self.fix()
        self._on_pick()

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None
        self._delete_button.disabled = self._list_view.value is None

    def _reload_list(self, new_value=None):
        self._list_view.options = self._model.get_summary()
        self._list_view.value = new_value

    def _add(self):
        self._model.current_id = None
        raise NextScene("Edit User")

    def _edit(self):
        self.save()
        self._model.current_id = self.data["users"]
        raise NextScene("Edit User")

    def _delete(self):
        self.save()
        self._model.delete_user(self.data["users"])
        self._reload_list()

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")


class UserView(Frame):
    def __init__(self, screen, model):
        super(UserView, self).__init__(screen,
                                          screen.height * 2 // 3,
                                          screen.width * 2 // 3,
                                          hover_focus=True,
                                          can_scroll=False,
                                          title="User Details",
                                          reduce_cpu=True)
        self._model = model 
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        self.nameBox = Text("Name:", "name")
        self.passBox = Text("Password:", "password", hide_char="*")
        self.repassBox = Text("Re-enter password:", "repassword", hide_char="*")
        layout.add_widget(self.nameBox)
        layout.add_widget(self.passBox)
        layout.add_widget(self.repassBox)
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        self.fix()

    def reset(self):
        # Do standard reset to clear out form, then populate with new data.
        super(UserView, self).reset()
        tmpData = self._model.get_current_user()
        self.data = {'name': tmpData['NAME'], 'id': tmpData['ID']}
        self.nameBox.readonly = True

    def _ok(self):
        self.save()
        error  = self._model.update_current_user(self.data)
        if error == -1:
            self._scene.add_effect(
                  PopUpDialog(self.screen, 'Empty user name', buttons = ['OK'], on_close=None, has_shadow=False, theme='warning'))
            return
        elif error == -2:
            self._scene.add_effect(
                  PopUpDialog(self.screen, 'Password do not match', buttons = ['OK'], on_close=None, has_shadow=False, theme='warning'))
            return
        elif error == -3:
            self._scene.add_effect(
                  PopUpDialog(self.screen, 'User exist!', buttons = ['OK'], on_close=None, has_shadow=False, theme='warning'))
            return
        raise NextScene("Main")

    @staticmethod
    def _cancel():
        raise NextScene("Main")


def demo(screen, scene):
    scenes = [
        Scene([ListView(screen, users)], -1, name="Main"),
        Scene([UserView(screen, users)], -1, name="Edit User")
    ]

    screen.play(scenes, stop_on_resize=True, start_scene=scene, allow_int=True)


users = UsertModel()
last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene

