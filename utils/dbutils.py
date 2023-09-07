"""
Database utilities
"""
from typing import AsyncIterator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine


class Database(object):
    """
    Database class for SQLite3.
    TODO: Potentially make a variable for table creation query
    """

    def __init__(self, db_name: str):
        """
        Database initialization logic
        :param db_name:
        TODO: use aiosqlite3
        """
        self.LocalSession = None
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{db_name}")

    def connect(self):
        """
        Initializes the database connection - creates an SQLAlchemy session
        :return:
        """
        self.LocalSession = async_sessionmaker(self.engine)

    def close(self):
        """
        Closes the database connection
        :return:
        """
        self.LocalSession.close()

    def get_session(self) -> AsyncIterator[async_sessionmaker]:
        try:
            yield self.LocalSession()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting session: {e}")

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


engine = create_async_engine("sqlite+aiosqlite:///filename")


class Base(AsyncAttrs, DeclarativeBase):
    pass
