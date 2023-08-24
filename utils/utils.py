"""
Contains utility functions for the project.
"""
import sqlite3


# TODO: tidy up this old class i'm reusing from as91892 - just adding this here as a 'base' for now.
class Database(object):
    """
    Database class for SQLite3.
    TODO: Potentially make a variable for table creation query
    """

    def __init__(self, db_name: str, init_query: str = r"query.sql"):
        """
        Database initialization logic
        :param db_name:
        TODO: use aiosqlite3
        """
        self.cursor = None
        self.connection = None
        self.db_name = db_name
        self.init_query = init_query

    def connect(self, execute_init: bool = True):
        """
        Connects to the database
        :return:
        """
        try:
            self.connection: sqlite3.Connection = sqlite3.connect(self.db_name)
            self.cursor: sqlite3.Cursor = self.connection.cursor()
            if execute_init:
                self.cursor.executescript(open(self.init_query, encoding="utf8").read())
        except sqlite3.Error as e:
            print(e)

    def close(self):
        """
        Closes the database connection
        :return:
        """
        self.connection.close()

    def read_db(self, query, params: tuple = (None,)) -> tuple:
        """
        Runs a query then fetches and returns output of the query.
        :param query:
        :param params:
        :return:
        """
        if params[0] is None and len(params) == 1:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)
        return tuple(self.cursor.fetchall())

    def get_all_fields_of_table(self, table) -> tuple:
        """
        Gets all columns (fields) excluding the id field, of a table using SQLite's PRAGMA command.
        Having this as a Python is more convenient than having it as a sqlite3 function
        :param table:
        :return:
        """
        self.cursor.execute(f"PRAGMA table_info({table});")
        row_info = self.cursor.fetchall()
        del row_info[0]
        data = []
        for val in row_info:
            data.append(val[1])
        return tuple(data)


class DatabaseError(Exception):
    """
    Custom exception for database errors.
    """

    def __init__(self, message: str) -> None:
        """
        Initialization logic for DatabaseError object
        :param message:
        """
        self.message = message


class Auditable(object):
    """
    Object containing information for an auditable event
    """

    def __init__(self, user: str, action: str, timestamp: str, data: str) -> None:
        """
        Initialization logic for Auditable object
        :param user:
        :param action:
        :param timestamp:
        :param data:
        """
        self.user = user
        self.action = action
        self.timestamp = timestamp
        self.data = data

    def __str__(self) -> str:
        """
        String representation of Auditable object
        :return:
        """
        return f"{self.user} {self.action} {self.timestamp} {self.data}"
