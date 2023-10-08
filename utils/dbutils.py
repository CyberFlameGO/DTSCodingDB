"""
Database utilities
"""
from typing import Optional
from collections.abc import AsyncGenerator

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
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

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Gets a session
        TODO: see https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/
         and https://fastapi.tiangolo.com/tutorial/dependencies/#what-is-dependency-injection
        """
        try:
            async with self.LocalSession() as session:
                # self.sessions.append(session)
                yield session
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting session: {e}")
        finally:
            await session.close()

    # async def disconnect(self):
    #     for session in self.sessions:
    #         if session.is_active():
    #             await session.close()

    @staticmethod
    async def insert(session: AsyncSession, model: Base):
        """
        Inserts a model into the database
        :param session:
        :param model:
        :return:
        """
        try:
            session.add(model)
            await session.commit()
            return
        except IntegrityError as e:
            raise DatabaseError(f"IntegrityError encountered whilst executing: {e}")
        except SQLAlchemyError as e:
            raise DatabaseError(f"SQLAlchemyError encountered whilst executing: {e}")


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
