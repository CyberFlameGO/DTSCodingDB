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
    match: Mapped[Set["Match"]] = relationship()
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
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    creator: Mapped[Set["Match"]] = relationship()
    player: Mapped[Set["MatchPlayers"]] = relationship(back_populates="player")


class Match(Base):
    __tablename__: str = "matches"

    id: Mapped[int] = mapped_column(autoincrement=True, nullable=False, unique=True, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    played_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    creator_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    players: Mapped[Set["MatchPlayers"]] = relationship(back_populates="match")
    results: Mapped["MatchResult"] = relationship(back_populates="match")


class MatchPlayers(Base):
    __tablename__: str = "matchplayers"

    id: Mapped[int] = mapped_column(autoincrement=True, nullable=False, unique=True, primary_key=True)

    match: Mapped["Match"] = relationship(back_populates="players")
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False)
    player: Mapped["User"] = relationship(back_populates="player")
    player_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


class MatchResult(Base):
    __tablename__: str = "matchresults"

    id: Mapped[int] = mapped_column(autoincrement=True, nullable=False, unique=True, primary_key=True)
    match: Mapped["Match"] = relationship(back_populates="results")
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), unique=True, nullable=False)

    won_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    lost_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    won: Mapped["User"] = relationship("User", foreign_keys=[won_id])
    lost: Mapped["User"] = relationship("User", foreign_keys=[lost_id])
