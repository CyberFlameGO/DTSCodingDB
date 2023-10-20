"""
Base class
"""
from datetime import UTC, datetime
from typing import Set

from sqlalchemy import ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for all models
    """

    __abstract__: bool = True
    id: Mapped[int] = mapped_column(autoincrement=True, nullable=False, unique=True, primary_key=True)


class Game(Base):
    __tablename__: str = "games"

    match: Mapped[Set["Match"]] = relationship(backref="game")
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[str] = mapped_column(nullable=False)


class User(Base):
    __tablename__: str = "users"

    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    year_level: Mapped[int] = mapped_column(nullable=True)
    house: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now(tz=UTC))

    creator: Mapped[Set["Match"]] = relationship()
    player: Mapped[Set["MatchPlayers"]] = relationship(back_populates="player")


class Match(Base):
    __tablename__: str = "matches"

    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    played_at: Mapped[datetime] = mapped_column(default=datetime.now(tz=UTC))

    creator_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(tz=UTC))
    players: Mapped[Set["MatchPlayers"]] = relationship(back_populates="match")
    results: Mapped["MatchResult"] = relationship(back_populates="match")


class MatchPlayers(Base):
    __tablename__: str = "matchplayers"

    match: Mapped["Match"] = relationship(back_populates="players")
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False)
    player: Mapped["User"] = relationship(back_populates="player")
    player_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


class MatchResult(Base):
    __tablename__: str = "matchresults"

    match: Mapped["Match"] = relationship(back_populates="results")
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), unique=True, nullable=False)

    won_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    lost_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    won: Mapped["User"] = relationship("User", foreign_keys=[won_id])
    lost: Mapped["User"] = relationship("User", foreign_keys=[lost_id])
