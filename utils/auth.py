from datetime import UTC, datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Annotated, Optional, Tuple

from models import User
from models.pydantic import PydanticUser, TokenData, UserInDB
from utils import Database


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_authdata(token: str):
    try:
        payload = jwt.decode(token, Auth.SECRET_KEY, algorithms=[Auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise Auth.credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise Auth.credentials_exception
    # fastapi dependency injection doesn't support what i'm trying to do well enough, so this is a nasty workaround
    return token_data


class Auth(object):
    # ideally this secret key would be an environment variable but for assessment simplicity it's here
    SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"

    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    @classmethod
    def verify_password(cls, plain_password, hashed_password):
        return cls.pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def get_password_hash(cls, password):
        return cls.pwd_context.hash(password)

    @staticmethod
    async def get_user_object(session, username: str):
        data = await Database.retrieve_by_field(session, User, User.username, username)
        if data:
            data_dict = data.__dict__
            data_dict.pop("_sa_instance_state", None)  # remove unwanted SQLAlchemy fields
            return UserInDB(**data_dict)

    @classmethod
    async def authenticate_user(cls, session, username: str, password: str):
        user = await cls.get_user_object(session, username)
        if not user:
            return False
        if not cls.verify_password(password, user.password):
            return False
        return user

    @classmethod
    def create_access_token(cls, data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def get_authorization_scheme_param(
        authorization_header_value: Optional[str],
    ) -> Tuple[str, str]:
        if not authorization_header_value:
            return "", ""
        scheme, _, param = authorization_header_value.partition(" ")
        return scheme, param
