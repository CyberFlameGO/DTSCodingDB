"""
Database utilities
"""
from collections.abc import AsyncIterator
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from models import Base


class Database(object):
    """
    Database class for SQLite3.
    TODO: Potentially make a variable for table creation query
    """

    def __init__(self, db_name: str):
        """
        Database initialization - call connect() to connect to the database
        :param db_name:
        TODO: use aiosqlite3
        """
        self._db_name: str = db_name
        self.engine: Optional[AsyncEngine] = None
        self.LocalSession: Optional[async_sessionmaker] = None
        # self.sessions: List = []

    async def connect(self):
        """
        Initializes the database connection - creates sessionmaker and engine
        :return:
        """
        self.engine: AsyncEngine = create_async_engine(f"sqlite+aiosqlite:///{self._db_name}")
        self.LocalSession: async_sessionmaker = async_sessionmaker(self.engine)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # await conn.run_sync(Base.metadata.reflect)

    async def get_session(self) -> AsyncIterator[AsyncSession]:
        """
        Gets a session
        """
        try:
            async with self.LocalSession() as session:
                # self.sessions.append(session)
                yield session
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting session: {e}")

    # async def disconnect(self):
    #     for session in self.sessions:
    #         if session.is_active():
    #             await session.close()


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
