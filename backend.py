import sqlite3
from typing import Any, Dict, cast
import uuid
import datetime

class UserData:
    dbpath = None
    """Database path for the SQLite database file. Do not modify directly, use the constructor to set this value."""
    
    cn = None
    """Connection object for the SQLite database. Do NOT modify directly, use the constructor to set this value."""
    
    cursor = None
    """Cursor object for the SQLite database. PLEASE DO NOT MODIFY directly, use the constructor to set this value."""
    
    user_data: Dict[str, str] = {"username": "", "id": ""}
    """Dictionary to store user data. Contains the following keys:
    "username": The username of the user.
    "id": The unique user ID generated based on the username.
    Do not modify directly, use the user_init() method to set these values."""
    
    grocery_data = []
    """List to store grocery data. Each item in the list is a dictionary with the following keys:
    "name": The name of the grocery item.
    "date": The date the item was added to the inventory.
    "category": The category of the grocery item.
    "expiry": The expiry date of the grocery item.
    Do not modify directly, something bad happens, use the add_item() and remove_item() methods to modify this list."""
    
    alr_init = False
    """Boolean flag to indicate whether the database has already been initialized. Set to True if the database has been initialized, False otherwise. Do not modify directly, use the constructor to set this value. Just trust me."""
    
    def __init__(self, dbpath):
        """The main class which handles most of the functions. Accepts a path to the database file."""

        self.dbpath = dbpath
        self.cn = sqlite3.connect(dbpath)
        self.cursor = self.cn.cursor()
        self.grocery_data = []
        self.user_data = {"username": "", "id": ""}

        try:
            # SQLite does not support Date objects, so use TEXT. So that I remember. :0
            self.cursor.execute("CREATE TABLE IF NOT EXISTS user_data (username TEXT, id TEXT);")
            self.cursor.execute("CREATE TABLE IF NOT EXISTS grocery_data (name TEXT, mfd_date TEXT, add_date TEXT, category TEXT, expiry TEXT, id TEXT);")
            self.cn.commit()
            self.cursor.execute("SELECT COUNT(*) FROM grocery_data;")
            if self.cursor.fetchone()[0] > 0:
                self.alr_init = True
                self.cursor.execute("SELECT name, mfd_date, add_date, category, expiry, id FROM grocery_data;")
                self.grocery_data = [
                    {
                        "name": row[0],
                        "mfd_date": row[1],
                        "add_date": row[2],
                        "category": row[3],
                        "expiry": row[4],
                        "id": row[5],
                    }
                    for row in self.cursor.fetchall()
                ]
                self.cursor.execute("SELECT username, id FROM user_data ORDER BY rowid DESC LIMIT 1;")
                user_row = self.cursor.fetchone()
                if user_row is not None:
                    self.user_data = {"username": user_row[0], "id": user_row[1]}
            else:
                self.alr_init = False
        except sqlite3.Error:
            self.alr_init = False
            self.user_data = {"username": "", "id": ""}
            self.grocery_data = []

    def user_init(self, username):
        """Initialises the user data and create a new user in the database. Accepts a permanent username and generates a unique user ID based on it."""
        self.user_data["username"] = username
        self.user_data["id"] = uuid.uuid3(uuid.NAMESPACE_DNS, username).hex
        assert self.cursor is not None
        self.cursor.execute("CREATE TABLE IF NOT EXISTS user_data (username TEXT, id TEXT);")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS grocery_data (name TEXT, mfd_date TEXT, add_date TEXT, category TEXT, expiry TEXT, id TEXT);")
        self.cursor.execute("INSERT INTO user_data (username, id) VALUES (?, ?);", (self.user_data["username"], self.user_data["id"]))
        assert self.cn is not None
        self.cn.commit()

    def get_user_data(self) -> Dict[str, str]:
        """Returns the user data as a dictionary."""
        return self.user_data
        
    def add_item(self, name, mfd_date, add_date, category, expiry):
        """Adds an item to the grocery data list. Accepts the name of the item, the date it was added, its category, and its expiry date."""
        self.grocery_data.append({"name": name, "mfd_date": mfd_date, "add_date": add_date, "category": category, "expiry": expiry, "id": uuid.uuid3(uuid.NAMESPACE_DNS, name).hex})
        
    def remove_item(self, name):
        """Removes an item from the grocery data list. Accepts the name of the item to be removed."""
        self.grocery_data = [item for item in self.grocery_data if item.get("name") != name]
        
    def check_expired(self):
        """Checks for expired items in the grocery data list. Returns a list of expired items."""
        items = []
        for item in self.grocery_data:
            if item["expiry"] < datetime.date.today().strftime("%Y-%m-%d"):
                items.append(item)
        return items
        
    def check_to_expire(self):
        """Checks for items that are about to expire in the grocery data list. Returns a list of items that are about to expire."""
        items = []
        for item in self.grocery_data:
            if item["expiry"] < (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d"):
                items.append(item)
        return items
        
    def push_to_db(self):
        """Pushes the user data and grocery data to the database in python."""

        assert self.cursor is not None
        assert self.cn is not None

        keys = ("name", "mfd_date", "add_date", "category", "expiry", "id")
        rows_to_insert = [tuple(d[key] for key in keys if key in d) for d in self.grocery_data]
        self.cursor.executemany("INSERT INTO grocery_data (name, mfd_date, add_date, category, expiry, id) VALUES (?, ?, ?, ?, ?, ?)", rows_to_insert)
        self.cn.commit()
        