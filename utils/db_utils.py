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
    Transactions are used for mutations to the database, but aren't deemed necessary (considering the use case) for
     accessing data, and no situation where they would be useful is likely to arise in the program.
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
            except IntegrityError:
                await session.rollback()
                raise  # re-raise
            except SQLAlchemyError:
                await session.rollback()
                raise  # re-raise
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
            except IntegrityError:
                await session.rollback()
                raise  # re-raise
            except SQLAlchemyError:
                await session.rollback()
                raise  # re-raise
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
        return await session.get(model, identifier)

    @staticmethod
    async def dump_all(session: AsyncSession, model: Type[Base]) -> Sequence[Base]:
        """
        Dumps all records for a model in the database TODO: finish writing function
        :param session:
        :param model:
        :return:
        """
        statement = select(model)
        executed = await session.execute(statement)
        return executed.scalars().all()

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
        statement = select(field, func.count("*").label(label)).group_by(field).order_by(func.count("*").desc())
        if limit is not None:
            statement = statement.limit(limit)
        executed = await session.execute(statement)
        return executed.all()

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
            except SQLAlchemyError:
                await session.rollback()
                raise  # re-raise
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Exception encountered whilst executing: {e}")

    @staticmethod
    async def has_existed(session: AsyncSession, model: Type[Base], identifier: int) -> bool:
        """
        Checks if a record has existed in the database, relying on the auto-incrementing primary key.
        There are various flaws with this method/implementation, but they are tolerable considering the method is
        only used to determine whether a response is 404 Not Found or 410 Gone
        :param identifier:
        :param session:
        :param model:
        :return:
        """
        statement = select(func.max(model.id))
        executed = await session.execute(statement)
        return executed.scalar() >= identifier


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