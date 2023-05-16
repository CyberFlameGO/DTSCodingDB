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

    def __init__(self, db_name: str, query_file: str = r"query.sql") -> None:
        """
        Database initialization logic
        :param db_name:
        """
        try:
            # Initialize the database (if it doesn't exist, a new file is created)
            self.connection = sqlite3.connect(db_name)
            # Set the cursor variable
            self.cursor = self.connection.cursor()
            # create a db table if it doesn't exist.
            # I'm aware that the autoincrement is redundant, as with having an 'id' column at all as
            # there's a built-in rowid which the id column just aliases to (unless using 'WITHOUT ROWID', which i'm not
            # doing right now as it's not worth the effort), but I've set it up this way on purpose.
            # Switching to no rowid is something I may do if I ever come back to working on this after submitting it.
            # todo: when i update these comments for this project, explain why i'm using real as opposed to
            #  double/float (the reason is that i don't need double precision decimals)
            self.cursor.executescript(open(query_file, 'r', encoding = "utf8").read())
        except sqlite3.Error as e:
            print(e)

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


class Role(object):
    """
    Object containing information for a role
    TODO: Decide if I want to do this as objects or write logic in each instance a role/permission is used
    """

    def __init__(self, name: str, permissions: list) -> None:
        """
        Initialization logic for Role object
        :param name:
        :param permissions:
        """
        self.name = name
        self.permissions = permissions


class User(object):
    """
    Object containing information for a user
    """

    def __init__(self, username: str, password: str, role: Role) -> None:
        """
        Initialization logic for User object
        :param username:
        :param password:
        :param role:
        """
        self.username = username
        self.password = password
        self.role = role


class Data(object):
    """
    Base class for all data objects (if they are to be pickled/serialised and stored as blob)
    """

    def __init__(self, data: dict) -> None:
        """
        Initialization logic for Data object
        :param data:
        """
        self.data = data

    def __str__(self) -> str:
        """
        String representation of Data object
        :return:
        """
        return str(self.data)
