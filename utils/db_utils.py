"""
Database utilities
"""
from typing import Optional, Sequence, Type
from collections.abc import AsyncGenerator

from sqlalchemy import update, select, delete, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from models import Base

type base_type = Type[Base]  # type alias for a base type


class Database(object):
    """
    Database class for SQLAlchemy.
    Record and row are used interchangeably as well as SQL terms being used interchangeably
     with object terms, where it sounds more natural.
    """

    def __init__(self, db_name: str):
        """
        Database initialization - call connect() to 'connect' to the database
        :param db_name:
        """
        self._db_name: str = db_name
        self.engine: Optional[AsyncEngine] = None
        self.LocalSession: Optional[async_sessionmaker] = None
        # self.sessions: List = []

    async def connect(self) -> None:
        """
         Initializes the database connection - creates sessionmaker and engine
         'connect' is a misleading term here, but calling it 'init' would be even more misleading so I've opted for this
         terminology.

        This method  may not appear necessary as its own method, as in it may appear better suited to the
         __init__ method, but __init__ cannot be async, and the engine needs to be awaited (even to synchronously create
         metadata).
         :return:
        """
        # Sets the engine and sessionmaker variables here - asmall way of making sure this method is called first
        self.engine: AsyncEngine = create_async_engine(f"sqlite+aiosqlite:///{self._db_name}")
        self.LocalSession: async_sessionmaker = async_sessionmaker(self.engine)
        # Creates the tables if they don't exist
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return None

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Yields a session
        """
        try:
            async with self.LocalSession() as session:
                # self.sessions.append(session)
                yield session
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting session: {e}")
        finally:
            if session:
                await session.close()

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
            await session.flush()
            model_id = model.id
            await session.commit()
            return model_id
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
        try:
            statement = update(model).where(model.id == identifier).values(data)
            await session.execute(statement)
            await session.commit()
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
    async def retrieve(session: AsyncSession, model: base_type, identifier: int) -> base_type:
        """
        Retrieves a record by primary key from a table in the database
        :param identifier:
        :param session:
        :param model:
        :return:
        """
        return await session.get_one(model, identifier)

    @staticmethod
    async def retrieve_by_field(session: AsyncSession, model: base_type, field, identifier) -> base_type:
        """
        Retrieves a record by field value from a table in the database
        Intended to retrieve only the first value (use-case: table with UNIQUE constraint)
        :param session:
        :param model:
        :param field: The field in model.field format
        :param identifier:
        :return:
        """
        # noinspection PyTypeChecker
        statement = select(model).where(field == identifier)
        executed = await session.execute(statement)
        return executed.scalar_one_or_none()

    @staticmethod
    async def dump_all(session: AsyncSession, model: base_type) -> Sequence[Base]:
        """
        Dumps all records for a model in the database
        :param session:
        :param model:
        :return:
        """
        statement = select(model)
        executed = await session.execute(statement)
        return executed.scalars().all()

    @staticmethod
    async def dump_by_field_descending(session: AsyncSession, field, label, limit: Optional[int] = None):
        """
        Dumps records by field in the database
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
    async def remove_record(session: AsyncSession, model: base_type, identifier: int):
        """
        Removes a record from the database
        :param session:
        :param model:
        :param identifier:
        :return:
        """
        try:
            statement = delete(model).where(model.id == identifier)
            await session.execute(statement)
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise  # re-raise
        except Exception as e:
            await session.rollback()
            raise DatabaseError(f"Exception encountered whilst executing: {e}")

    @staticmethod
    async def has_existed(session: AsyncSession, model: base_type, identifier: int) -> bool:
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
