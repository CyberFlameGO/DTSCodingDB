"""
Pydantic models. Code can't reasonably be reduced here - SQLModel (library) would've been an ideal candidate but as
said elsewhere in the code (in a different file) in the project, it isn't compatible with my versions of
SQLAlchemy and Pydantic.
Comments aren't really necessary in here - the code is pretty self-explanatory.
"""
from datetime import UTC, datetime
from pydantic import BaseModel


# SQLModel would reduce the duplicated code greatly here and follow DRY, but it isn't compatible with my versions of
# SQLAlchemy and Pydantic - there isn't much I can do to reduce it easily, but it is worth noting.
class PydanticUser(BaseModel):
    id: int
    email: str
    username: str
    role: str
    first_name: str
    last_name: str
    year_level: int
    house: str

    created_at: datetime = datetime.now(tz=UTC)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserInDB(PydanticUser):
    password: str
