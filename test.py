import asyncio

from fastapi import Depends

from utils import *
from models import *


async def main():
    db = Database("data.db")
    await db.connect()
    print("d")
    async for session in db.get_session():
        session.add(Game(id=6, name="penis", description="Penis"))
        await session.commit()
        print("dd")


if __name__ == "__main__":
    asyncio.run(main())
