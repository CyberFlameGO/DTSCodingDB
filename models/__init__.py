"""
Base class
"""
from datetime import datetime
from typing import Set

from sqlalchemy import ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for all models
    """

    __abstract__: bool = True


class Game(Base):
    __tablename__: str = "games"

    id: Mapped[int] = mapped_column(autoincrement=True, nullable=False, unique=True, primary_key=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()


class User(Base):
    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(autoincrement=True, nullable=False, unique=True, primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(unique=True, nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)
    first_name: Mapped[str] = mapped_column()
    last_name: Mapped[str] = mapped_column()
    games_played: Mapped[int] = mapped_column()
    games_won: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Match(Base):
    __tablename__: str = "matches"

    id: Mapped[int] = mapped_column(autoincrement=True, nullable=False, unique=True, primary_key=True)
    game_type: Mapped[str] = mapped_column()
    played_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    creator: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    players: Mapped[Set["MatchPlayers"]] = relationship(back_populates="match")


class MatchPlayers(Base):
    __tablename__: str = "matchplayers"

    id: Mapped[int] = mapped_column(autoincrement=True, nullable=False, unique=True, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    match: Mapped["Match"] = relationship(back_populates="players")
    player_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class MatchResult(Base):
    __tablename__: str = "matchresults"

    id: Mapped[int] = mapped_column(autoincrement=True, nullable=False, unique=True, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    won: Mapped[str] = mapped_column()
    lost: Mapped[str] = mapped_column()