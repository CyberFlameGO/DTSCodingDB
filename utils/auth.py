from datetime import UTC, datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Annotated

from models import User
from models.pydantic import PydanticUser, TokenData, UserInDB
from utils import Database


class Auth(object):
    # class level constants
    SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    OAuth2_Scheme = Annotated[str, Depends(oauth2_scheme)]
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
    async def get_user(session, username: str):
        data = await Database.retrieve_by_field(session, User, User.username, username)
        if data:
            data_dict = data.__dict__
            data_dict.pop('_sa_instance_state', None)  # remove unwanted SQLAlchemy fields
            return UserInDB(**data_dict)

    @classmethod
    async def authenticate_user(cls, session, username: str, password: str):
        user = await cls.get_user(session, username)
        if not user:
            return False
        if not cls.verify_password(password, user.hashed_password):
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

    @classmethod
    async def get_current_user(cls, session, token: str):
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise cls.credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise cls.credentials_exception
        user = await cls.get_user(session, username=token_data.username)
        if user is None:
            raise cls.credentials_exception
        return user

    @staticmethod
    async def get_current_active_user(current_user: PydanticUser):
        if current_user.disabled:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
