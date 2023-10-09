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
        session.add(User(id=1, email="test@test.com", username="test", password="test", role="test"))
        session.add(User(id=2, email="twst@test.com", username="twst", password="twst", role="twst"))
        session.add(Game(name="test", description="test"))
        session.add(
            Match(
                game_type="test",
                creator="test",
                players=[MatchPlayers(player=User(id=1)), MatchPlayers(player=User(id=2))],
                results=[MatchResult(winner=User(id=1), loser=User(id=2))],
                played_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )
        )
        await session.commit()
        print("dd")


if __name__ == "__main__":
    asyncio.run(main())
