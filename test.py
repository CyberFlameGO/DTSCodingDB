import asyncio

from fastapi import Depends

from utils import *
from models import *


async def main():
    db = Database("data.db")
    await db.connect()
    print("d")
    print(type(db.get_session()))
    async for session in db.get_session():
        print(type(session))
        return
        session.add(Game(id=6, name="test", description="Tennis"))
        await session.commit()
        print("dd")


if __name__ == "__main__":
    asyncio.run(main())