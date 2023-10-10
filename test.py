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
        session.add(
            User(
                id=1,
                email="test@test.com",
                username="test",
                password="test",
                first_name="test",
                last_name="test",
                role="test",
            )
        )
        session.add(
            User(
                id=2,
                email="twst@test.com",
                username="twst",
                password="twst",
                role="twst",
                first_name="twst",
                last_name="twst",
            )
        )
        session.add(Game(id=1, name="test", description="test"))
        await session.commit()
        print("dd")
        session.add(
            Match(
                game_id=1,
                creator_id=1,
                players={MatchPlayers(player_id=1), MatchPlayers(player_id=2)},
                results=MatchResult(won_id=1, lost_id=2),
            )
        )
        await session.commit()
        print("done")


if __name__ == "__main__":
    asyncio.run(main())
