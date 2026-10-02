import sqlite3
import uuid
import datetime

class UserData:
    dbpath = None
    """Database path for the SQLite database file. Do not modify directly, use the constructor to set this value."""
    
    cn =None
    """Connection object for the SQLite database. Do not modify directly, use the constructor to set this value."""
    
    cursor =None
    """Cursor object for the SQLite database. Do not modify directly, use the constructor to set this value."""
    
    user_data = {}
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
    Do not modify directly, use the add_item() and remove_item() methods to modify this list."""
    
    alr_init =False
    """Boolean flag to indicate whether the database has already been initialized. Set to True if the database has been initialized, False otherwise. Do not modify directly, use the constructor to set this value."""
    
    def __init__(self, dbpath):
        """The main class which handles most of the functions. Accepts a path to the database file."""
        self.dbpath = dbpath
        self.cn = sqlite3.connect(dbpath)
        self.cursor =self.cn.cursor()
        self.cursor.execute("SELECT count(grocery_data) FROM sqlite_master WHERE type='table';")
        if self.cursor.fetchone():
            self.alr_init =True
            self.cursor.execute("SELECT * FROM grocery_data;")
            self.grocery_data =self.cursor.fetchall()
            self.cursor.execute("SELECT * FROM user_data;")
            self.user_data =self.cursor.fetchall()
        else:
            self.alr_init = False
    def user_init(self, username):
        """Initialises the user data and create a new user in the database. Accepts a permanent username and generates a unique user ID based on it."""
        self.user_data["username"] = username
        self.user_data["id"] = uuid.uuid3(uuid.NAMESPACE_DNS, username).hex
        
    def add_item(self, name, mfd_date, add_date, category, expiry):
        """Adds an item to the grocery data list. Accepts the name of the item, the date it was added, its category, and its expiry date."""
        self.grocery_data.append({"name": name, "mfd_date": mfd_date, "add_date": add_date, "category": category, "expiry": expiry, "id": uuid.uuid3(uuid.NAMESPACE_DNS, name).hex})
        
    def remove_item(self, name):
        """Removes an item from the grocery data list. Accepts the name of the item to be removed."""
        self.grocery_data.remove({"name": name})
        
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
            if item["expiry"] < (datetime.datetime.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d"):
                items.append(item)
        return items
        
    def push_to_db(self):
        """Pushes the user data and grocery data to the database in python."""
        keys = ("name", "role", "city")
        rows_to_insert = [tuple(d[key] for key in keys) for d in self.grocery_data]
        self.cursor.executemany("INSERT INTO employees (name, role, city) VALUES (%s, %s, %s)", rows_to_insert)
        