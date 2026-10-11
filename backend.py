##import sqlite3
##from typing import Dict, List
##import uuid
##import datetime
##
##
##class UserData:
##
##    def __init__(self, dbpath):
##        self.dbpath = dbpath
##        self.cn = sqlite3.connect(dbpath)
##        self.cursor = self.cn.cursor()
##
##        self.grocery_data: List[Dict] = []
##        self.user_data = {"username": "", "id": ""}
##
##        self.alr_init = False
##        self.is_dirty = False
##
##        self.initialize_database()
##        
##    def remove_item(self, item_id):
##        """Remove one item from the current user's inventory."""
##
##        user = self.get_user_data()
##
##        if not user:
##            return False
##
##        user_id = user["id"]
##
##        # Remove only the selected item belonging to this user.
##        self.grocery_data = [
##            item
##            for item in self.grocery_data
##            if str(item["id"]) != str(item_id)
##        ]
##
##        with self.connection:
##            self.connection.execute(
##                """
##                DELETE FROM grocery_data
##                WHERE id = ? AND user_id = ?
##                """,
##                (item_id, user_id),
##            )
##
##        return True
##
##
##    # =========================================================
##    # DATABASE INITIALIZATION
##    # =========================================================
##
##    def initialize_database(self):
##
##        assert self.cursor is not None
##        assert self.cn is not None
##
##        try:
##
##            # -------------------------------------------------
##            # USER TABLE
##            # -------------------------------------------------
##
##            self.cursor.execute("""
##                CREATE TABLE IF NOT EXISTS user_data (
##                    username TEXT,
##                    id TEXT
##                );
##            """)
##
##            # -------------------------------------------------
##            # GROCERY TABLE
##            # -------------------------------------------------
##
##            self.cursor.execute("""
##                CREATE TABLE IF NOT EXISTS grocery_data (
##                    name TEXT,
##                    mfd_date TEXT,
##                    add_date TEXT,
##                    category TEXT,
##                    expiry TEXT,
##                    id TEXT
##                );
##            """)
##
##            # -------------------------------------------------
##            # ADD user_id COLUMN IF IT DOES NOT EXIST
##            # -------------------------------------------------
##
##            self.cursor.execute(
##                "PRAGMA table_info(grocery_data);"
##            )
##
##            columns = [
##                column[1]
##                for column in self.cursor.fetchall()
##            ]
##
##            if "user_id" not in columns:
##
##                self.cursor.execute(
##                    "ALTER TABLE grocery_data "
##                    "ADD COLUMN user_id TEXT;"
##                )
##
##            self.cn.commit()
##
##            # -------------------------------------------------
##            # LOAD MOST RECENT USER
##            # -------------------------------------------------
##
##            self.cursor.execute("""
##                SELECT username, id
##                FROM user_data
##                ORDER BY rowid DESC
##                LIMIT 1;
##            """)
##
##            user_row = self.cursor.fetchone()
##
##            if user_row is not None:
##
##                self.user_data = {
##                    "username": user_row[0],
##                    "id": user_row[1],
##                }
##
##                self.alr_init = True
##
##                # -------------------------------------------------
##                # MIGRATE OLD INVENTORY
##                #
##                # Old items did not have a user_id.
##                # If there are any, assign them to the most
##                # recently created account.
##                # -------------------------------------------------
##
##                self.cursor.execute("""
##                    UPDATE grocery_data
##                    SET user_id = ?
##                    WHERE user_id IS NULL;
##                """, (self.user_data["id"],))
##
##                self.cn.commit()
##
##                self.load_inventory()
##
##            else:
##
##                self.user_data = {
##                    "username": "",
##                    "id": "",
##                }
##
##                self.grocery_data = []
##
##                self.alr_init = False
##
##        except sqlite3.Error:
##
##            self.alr_init = False
##
##            self.user_data = {
##                "username": "",
##                "id": "",
##            }
##
##            self.grocery_data = []
##
##    # =========================================================
##    # LOAD CURRENT USER'S INVENTORY
##    # =========================================================
##
##    def load_inventory(self):
##
##        assert self.cursor is not None
##
##        if not self.user_data["id"]:
##
##            self.grocery_data = []
##            return
##
##        self.cursor.execute("""
##            SELECT
##                name,
##                mfd_date,
##                add_date,
##                category,
##                expiry,
##                id
##            FROM grocery_data
##            WHERE user_id = ?
##            ORDER BY rowid;
##        """, (self.user_data["id"],))
##
##        rows = self.cursor.fetchall()
##
##        self.grocery_data = [
##            {
##                "name": row[0],
##                "mfd_date": row[1],
##                "add_date": row[2],
##                "category": row[3],
##                "expiry": row[4],
##                "id": row[5],
##            }
##            for row in rows
##        ]
##
##        self.is_dirty = False
##
##    # =========================================================
##    # CHECK IF USER EXISTS
##    # =========================================================
##
##    def user_exists(self, username):
##
##        assert self.cursor is not None
##
##        self.cursor.execute(
##            """
##            SELECT 1
##            FROM user_data
##            WHERE username = ? COLLATE NOCASE
##            LIMIT 1;
##            """,
##            (username.strip(),),
##        )
##
##        return self.cursor.fetchone() is not None
##
##    # =========================================================
##    # LOGIN
##    # =========================================================
##
##    def login_user(self, username):
##
##        assert self.cursor is not None
##
##        username = username.strip()
##
##        self.cursor.execute(
##            """
##            SELECT username, id
##            FROM user_data
##            WHERE username = ? COLLATE NOCASE
##            ORDER BY rowid DESC
##            LIMIT 1;
##            """,
##            (username,),
##        )
##
##        user_row = self.cursor.fetchone()
##
##        if user_row is None:
##            return False
##
##        # Set current user
##        self.user_data = {
##            "username": user_row[0],
##            "id": user_row[1],
##        }
##
##        self.alr_init = True
##
##        # VERY IMPORTANT:
##        # Load ONLY this user's inventory.
##        self.load_inventory()
##
##        return True
##
##    # =========================================================
##    # CREATE NEW USER
##    # =========================================================
##
##    def user_init(self, username):
##
##        assert self.cursor is not None
##        assert self.cn is not None
##
##        username = username.strip()
##
##        user_id = uuid.uuid3(
##            uuid.NAMESPACE_DNS,
##            username
##        ).hex
##
##        self.user_data = {
##            "username": username,
##            "id": user_id,
##        }
##
##        self.cursor.execute(
##            """
##            INSERT INTO user_data
##            (username, id)
##            VALUES (?, ?);
##            """,
##            (
##                username,
##                user_id,
##            ),
##        )
##
##        self.cn.commit()
##
##        self.alr_init = True
##
##        # A new account starts with an EMPTY inventory.
##        self.grocery_data = []
##
##        self.is_dirty = False
##
##    # =========================================================
##    # GET USER DATA
##    # =========================================================
##
##    def get_user_data(self):
##
##        return self.user_data
##
##    # =========================================================
##    # ADD ITEM
##    # =========================================================
##
##    def add_item(
##        self,
##        name,
##        mfd_date,
##        add_date,
##        category,
##        expiry,
##    ):
##
##        if not self.user_data["id"]:
##            return
##
##        item = {
##            "name": name.lower(),
##            "mfd_date": mfd_date,
##            "add_date": add_date,
##            "category": category,
##            "expiry": expiry,
##
##            # Use a unique ID for every item.
##            "id": uuid.uuid4().hex,
##        }
##
##        self.grocery_data.append(item)
##
##        self.is_dirty = True
##
##    # =========================================================
##    # REMOVE ITEM
##    # =========================================================
##
##    def remove_item(self, name):
##
##        self.grocery_data = [
##            item
##            for item in self.grocery_data
##            if item.get("name") != name.lower()
##        ]
##
##        self.is_dirty = True
##
##    # =========================================================
##    # CHECK EXPIRED
##    # =========================================================
##
##    def check_expired(self):
##
##        items = []
##
##        today = datetime.date.today().strftime("%Y-%m-%d")
##
##        for item in self.grocery_data:
##
##            if item["expiry"] < today:
##                items.append(item)
##
##        return items
##
##    # =========================================================
##    # CHECK ITEMS ABOUT TO EXPIRE
##    # =========================================================
##
##    def check_to_expire(self):
##
##        items = []
##
##        tomorrow = (
##            datetime.date.today()
##            + datetime.timedelta(days=1)
##        ).strftime("%Y-%m-%d")
##
##        for item in self.grocery_data:
##
##            if item["expiry"] < tomorrow:
##                items.append(item)
##
##        return items
##
##    # =========================================================
##    # SAVE CURRENT USER'S INVENTORY
##    # =========================================================
##
##    def push_to_db(self):
##
##        assert self.cursor is not None
##        assert self.cn is not None
##
##        if not self.is_dirty:
##            return
##
##        if not self.user_data["id"]:
##            return
##
##        current_user_id = self.user_data["id"]
##
##        # -----------------------------------------------------
##        # DELETE ONLY THIS USER'S ITEMS
##        # -----------------------------------------------------
##
##        self.cursor.execute(
##            """
##            DELETE FROM grocery_data
##            WHERE user_id = ?;
##            """,
##            (current_user_id,),
##        )
##
##        # -----------------------------------------------------
##        # INSERT THIS USER'S ITEMS
##        # -----------------------------------------------------
##
##        rows_to_insert = []
##
##        for item in self.grocery_data:
##
##            rows_to_insert.append(
##                (
##                    item["name"],
##                    item["mfd_date"],
##                    item["add_date"],
##                    item["category"],
##                    item["expiry"],
##                    item["id"],
##                    current_user_id,
##                )
##            )
##
##        if rows_to_insert:
##
##            self.cursor.executemany(
##                """
##                INSERT INTO grocery_data
##                (
##                    name,
##                    mfd_date,
##                    add_date,
##                    category,
##                    expiry,
##                    id,
##                    user_id
##                )
##                VALUES (?, ?, ?, ?, ?, ?, ?);
##                """,
##                rows_to_insert,
##            )
##
##        self.cn.commit()
##
##        self.is_dirty = False


import sqlite3
import threading
import uuid
import datetime
from typing import Dict, List, Optional


DATE_FORMAT = "%Y-%m-%d"


def _parse_date(value: str) -> datetime.date:
    """Parse a YYYY-MM-DD string. Raises ValueError if it is not valid."""
    try:
        return datetime.datetime.strptime(str(value).strip(), DATE_FORMAT).date()
    except ValueError:
        raise ValueError(
            f"Invalid date '{value}'. Dates must be in YYYY-MM-DD format."
        )


class UserData:
    """
    ShelfSense backend: users, grocery inventory, expiry checks (SQLite).

    Every change to the inventory is saved to the database straight away,
    so data survives closing the app. push_to_db() is kept so existing
    UI code that calls it keeps working.
    """

    # An item counts as "about to expire" if it expires within this many days.
    DEFAULT_WARNING_DAYS = 3

    def __init__(self, dbpath):
        self.dbpath = dbpath

        # check_same_thread=False because Flet may call us from different threads; the lock below keeps access safe.
        self.cn = sqlite3.connect(dbpath, check_same_thread=False)
        self.cursor = self.cn.cursor()
        self._lock = threading.RLock()

        self.grocery_data: List[Dict] = []
        self.user_data = {"username": "", "id": ""}

        self.alr_init = False   # True once a user exists / is logged in
        self.is_dirty = False   # kept for compatibility (always False now)

        self.initialize_database()

    # =========================================================
    # DATABASE INITIALISATION TIME!!
    # =========================================================

    def initialize_database(self):
        with self._lock:
            # ---- user table ----
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_data (
                    username TEXT,
                    id TEXT
                );
            """)

            # ---- grocery table ----
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS grocery_data (
                    name TEXT,
                    mfd_date TEXT,
                    add_date TEXT,
                    category TEXT,
                    expiry TEXT,
                    id TEXT
                );
            """)

            # ---- add user_id column to older databases ----
            self.cursor.execute("PRAGMA table_info(grocery_data);")
            columns = [col[1] for col in self.cursor.fetchall()]
            if "user_id" not in columns:
                self.cursor.execute(
                    "ALTER TABLE grocery_data ADD COLUMN user_id TEXT;"
                )

            self.cn.commit()

            # ---- load most recent user ----
            self.cursor.execute("""
                SELECT username, id
                FROM user_data
                ORDER BY rowid DESC
                LIMIT 1;
            """)
            user_row = self.cursor.fetchone()

            if user_row is None:
                self._clear_session()
                return

            self.user_data = {"username": user_row[0], "id": user_row[1]}
            self.alr_init = True

            # Old items had no user_id: give them to the latest account.
            self.cursor.execute(
                "UPDATE grocery_data SET user_id = ? WHERE user_id IS NULL;",
                (self.user_data["id"],),
            )
            self.cn.commit()

            self.load_inventory()

    def _clear_session(self):
        self.user_data = {"username": "", "id": ""}
        self.grocery_data = []
        self.alr_init = False
        self.is_dirty = False

    # =========================================================
    # LOAD CURRENT USER'S INVENTORY
    # =========================================================

    def load_inventory(self):
        with self._lock:
            if not self.user_data["id"]:
                self.grocery_data = []
                return

            self.cursor.execute(
                """
                SELECT name, mfd_date, add_date, category, expiry, id
                FROM grocery_data
                WHERE user_id = ?
                ORDER BY rowid;
                """,
                (self.user_data["id"],),
            )

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
            self.is_dirty = False

    # =========================================================
    # USERS
    # =========================================================

    def user_exists(self, username: str) -> bool:
        with self._lock:
            self.cursor.execute(
                """
                SELECT 1
                FROM user_data
                WHERE username = ? COLLATE NOCASE
                LIMIT 1;
                """,
                (username.strip(),),
            )
            return self.cursor.fetchone() is not None

    def login_user(self, username: str) -> bool:
        """Switch to an existing user. Returns False if the user is unknown."""
        with self._lock:
            self.cursor.execute(
                """
                SELECT username, id
                FROM user_data
                WHERE username = ? COLLATE NOCASE
                ORDER BY rowid DESC
                LIMIT 1;
                """,
                (username.strip(),),
            )
            user_row = self.cursor.fetchone()

            if user_row is None:
                return False

            self.user_data = {"username": user_row[0], "id": user_row[1]}
            self.alr_init = True

            # Load ONLY this user's inventory.
            self.load_inventory()
            return True

    def user_init(self, username: str):
        """
        Create a new user with a unique ID and an empty inventory.
        Raises ValueError if the username is empty or already taken.
        """
        username = username.strip()

        if not username:
            raise ValueError("Username cannot be empty.")

        with self._lock:
            if self.user_exists(username):
                raise ValueError(f"Username '{username}' is already taken.")

            user_id = uuid.uuid4().hex

            self.cursor.execute(
                "INSERT INTO user_data (username, id) VALUES (?, ?);",
                (username, user_id),
            )
            self.cn.commit()

            self.user_data = {"username": username, "id": user_id}
            self.alr_init = True
            self.grocery_data = []
            self.is_dirty = False

    def get_user_data(self):
        return self.user_data

    # =========================================================
    # ADD ITEM
    # =========================================================

    def add_item(
        self,
        name,
        mfd_date,
        add_date=None,
        category="Other",
        expiry=None,
    ):
        """
        Add an item to the current user's inventory and save it.

        - add_date is set automatically to today. The parameter is only
          kept so older calls like add_item(name, mfd, add, cat, exp)
          don't break; whatever is passed is ignored.
        - Raises ValueError for empty names, bad date formats, or an
          expiry date earlier than the manufacture date.

        Returns the new item (a dict).
        """
        if not self.user_data["id"]:
            raise ValueError("No user is set up yet.")

        name = (name or "").strip().lower()
        if not name:
            raise ValueError("Item name cannot be empty.")

        if not mfd_date or not expiry:
            raise ValueError("Manufacture date and expiry date are required.")

        mfd = _parse_date(mfd_date)
        exp = _parse_date(expiry)

        if exp < mfd:
            raise ValueError(
                "Expiry date cannot be earlier than the manufacture date."
            )

        item = {
            "name": name,
            "mfd_date": mfd.isoformat(),
            "add_date": datetime.date.today().isoformat(),
            "category": (category or "Other").strip(),
            "expiry": exp.isoformat(),
            "id": uuid.uuid4().hex,
        }

        with self._lock:
            self.cursor.execute(
                """
                INSERT INTO grocery_data
                (name, mfd_date, add_date, category, expiry, id, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    item["name"],
                    item["mfd_date"],
                    item["add_date"],
                    item["category"],
                    item["expiry"],
                    item["id"],
                    self.user_data["id"],
                ),
            )
            self.cn.commit()
            self.grocery_data.append(item)

        return item

    # =========================================================
    # REMOVE ITEM (by item id)
    # =========================================================

    def remove_item(self, item_id) -> bool:
        """
        Remove ONE item, identified by its unique id, from the current
        user's inventory. Returns True if something was removed.
        """
        user_id = self.user_data["id"]
        if not user_id:
            return False

        with self._lock:
            self.cursor.execute(
                "DELETE FROM grocery_data WHERE id = ? AND user_id = ?;",
                (str(item_id), user_id),
            )
            self.cn.commit()
            removed = self.cursor.rowcount > 0

            if removed:
                self.grocery_data = [
                    i for i in self.grocery_data
                    if str(i["id"]) != str(item_id)
                ]

            return removed

    # =========================================================
    # EXPIRY CHECKS
    # =========================================================

    def check_expired(self) -> List[Dict]:
        """Items whose expiry date is before today."""
        today = datetime.date.today()
        result = []

        for item in self.grocery_data:
            try:
                if _parse_date(item["expiry"]) < today:
                    result.append(item)
            except ValueError:
                continue  # skip items with unreadable dates

        return sorted(result, key=lambda i: i["expiry"])

    def check_to_expire(self, days: Optional[int] = None) -> List[Dict]:
        """
        Items that have NOT expired yet but will within `days` days
        (today counts). Expired items are not included here.
        """
        if days is None:
            days = self.DEFAULT_WARNING_DAYS

        today = datetime.date.today()
        limit = today + datetime.timedelta(days=days)
        result = []

        for item in self.grocery_data:
            try:
                if today <= _parse_date(item["expiry"]) <= limit:
                    result.append(item)
            except ValueError:
                continue

        return sorted(result, key=lambda i: i["expiry"])

    # =========================================================
    # COMPATIBILITY / CLEANUP
    # =========================================================

    def push_to_db(self):
        """
        Kept so existing UI code doesn't break. Changes are already saved
        immediately by add_item/remove_item, so this just commits.
        """
        with self._lock:
            self.cn.commit()
            self.is_dirty = False

    def close(self):
        with self._lock:
            self.cn.commit()
            self.cn.close()
