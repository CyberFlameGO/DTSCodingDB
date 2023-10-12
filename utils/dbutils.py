"""
Database utilities
"""
from typing import Optional, Sequence, Type
from collections.abc import AsyncGenerator

from sqlalchemy import update, select, delete, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from models import Base


class Database(object):
    """
    Database class for SQLite3.
    Record and row are used interchangeably as well as SQL terms being used interchangeably
     with object terms, where it sounds more natural.
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

    async def connect(self) -> None:
        """
        Initializes the database connection - creates sessionmaker and engine
        :return:
        """
        self.engine: AsyncEngine = create_async_engine(f"sqlite+aiosqlite:///{self._db_name}")
        self.LocalSession: async_sessionmaker = async_sessionmaker(self.engine)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # await conn.run_sync(Base.metadata.reflect)
        return None

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

    @staticmethod
    async def insert(session: AsyncSession, model: Base):
        """
        Inserts a model into the database
        :param session:
        :param model:
        :return:
        """
        async with session.begin():
            try:
                session.add(model)
            except IntegrityError as e:
                await session.rollback()
                raise DatabaseError(f"IntegrityError encountered whilst executing: {e}")
            except SQLAlchemyError as e:
                await session.rollback()
                raise DatabaseError(f"SQLAlchemyError encountered whilst executing: {e}")
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Exception encountered whilst executing: {e}")

    @staticmethod
    async def update(session: AsyncSession, model: Type[Base], identifier: int, data: dict):
        """
        Updates a row in the database
        :param data:
        :param session:
        :param model:
        :param identifier:
        :return:
        """
        async with session.begin():
            try:
                statement = update(model).where(model.id == identifier).values(data)
                await session.execute(statement)
            except IntegrityError as e:
                await session.rollback()
                raise DatabaseError(f"IntegrityError encountered whilst executing: {e}")
            except SQLAlchemyError as e:
                await session.rollback()
                raise DatabaseError(f"SQLAlchemyError encountered whilst executing: {e}")
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Exception encountered whilst executing: {e}")

    @staticmethod
    async def retrieve(session: AsyncSession, model: Type[Base], identifier: int) -> Optional[Base]:
        """
        Retrieves a record by primary key from a table in the database TODO: adjust return type
        :param identifier:
        :param session:
        :param model:
        :return:
        """
        try:
            return await session.get(model, identifier)
        except SQLAlchemyError as e:
            raise DatabaseError(f"SQLAlchemyError encountered whilst executing: {e}")

    @staticmethod
    async def dump_all(session: AsyncSession, model: Type[Base]) -> Sequence[Base]:
        """
        Dumps all records for a model in the database TODO: finish writing function
        :param session:
        :param model:
        :return:
        """
        try:
            statement = select(model)
            executed = await session.execute(statement)
            return executed.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"SQLAlchemyError encountered whilst executing: {e}")

    @staticmethod
    async def dump_by_field_descending(session: AsyncSession, field, label, limit: int | None = None):
        """
        Dumps records by field in the database TODO: finish writing function
        :param session:
        :param field: The field in model.field format
        :param label: A label
        :param limit: Optional limit of records to fetch
        :return:
        """
        try:
            statement = select(field, func.count("*").label(label)).group_by(field).order_by(func.count("*").desc())
            if limit is not None:
                statement = statement.limit(limit)
            executed = await session.execute(statement)
            return executed.all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"SQLAlchemyError encountered whilst executing: {e}")

    @staticmethod
    async def remove_record(session: AsyncSession, model: Type[Base], identifier: int):
        """
        Removes a record from the database
        :param session:
        :param model:
        :param identifier:
        :return:
        """
        async with session.begin():
            try:
                statement = delete(model).where(model.id == identifier)
                await session.execute(statement)
            except SQLAlchemyError as e:
                await session.rollback()
                raise DatabaseError(f"SQLAlchemyError encountered whilst executing: {e}")
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Exception encountered whilst executing: {e}")


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
