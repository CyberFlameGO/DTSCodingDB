from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Annotated, Tuple, Type

import sentry_sdk
from fastapi import Depends, FastAPI, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

import models
import utils
from models import Base, Game, PydanticUser, Token, User

sentry_sdk.init(
    dsn="https://eebca21dd9c9418cbfe83e7b8a0976de@o317122.ingest.sentry.io/4504873492480000",
    send_default_pii=True,
    traces_sample_rate=1.0,
    _experiments={
        "profiles_sample_rate": 1.0,
    },
)

templates = Jinja2Templates(directory="templates")
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

db = utils.Database("data.db")  # TODO: setup database tables and re-jig the spreadsheet layout

Auth = utils.Auth
Session = Annotated[AsyncSession, Depends(db.get_session)]
Current_Active_User = Annotated[PydanticUser, Depends(Auth.get_current_active_user)]


class Endpoint(Enum):
    """
    Enum of endpoints
    """
    GAMES = "games"
    LOGIN = "login"
    REGISTER = "register"


def classify(to_classify: Endpoint | str) -> tuple[Type[Base], Endpoint] | tuple[None, int]:
    """
    Abstracts endpoint classification away from route function
    :param to_classify:
    :return:
    """
    try:
        subject = Endpoint(to_classify)
    except ValueError:
        return None, status.HTTP_404_NOT_FOUND
    match subject:
        case Endpoint.GAMES:
            return models.Game, subject
        case Endpoint.LOGIN | Endpoint.REGISTER:
            return models.User, subject
        case _:
            return None, status.HTTP_404_NOT_FOUND


@app.on_event("startup")
async def startup():
    await db.connect()


@app.on_event("shutdown")
async def shutdown():
    pass


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Home page
    :param request:
    :return:
    """
    for route in app.routes:
        print(route)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


@app.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Session,
):
    user = await Auth.authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=Auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = Auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=PydanticUser)
async def read_users_me(
        current_user: Current_Active_User
):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(
        current_user: Current_Active_User
):
    return [{"item_id": "Foo", "owner": current_user.username}]



@app.get("/{endpoint}", response_class=HTMLResponse)
async def records_list(request: Request, session: Session, endpoint: str):
    """
    Games page
    :param endpoint:
    :param session:
    :param request:
    :return:
    """
    model, endpoint_type = classify(endpoint)
    if model is None:
        return Response(status_code = status.HTTP_404_NOT_FOUND)
    context: dict = {
        "request": request,
    }
    match endpoint_type:
        case Endpoint.GAMES:
            context["games"] = await db.dump_all(session, model)
            context["can_mutate"] = True
        case _:
            pass
    return templates.TemplateResponse(
        f"{endpoint_type.value}.html",
        context,
    )


@app.post("/{endpoint}", response_class=HTMLResponse)
async def new_record(request: Request, session: Session, endpoint: str):
    """
    New game page
    :param endpoint:
    :param request:
    :param session:
    :return:
    """
    # This code gets the form data from the request
    form = await request.form()
    print(form)
    model, endpoint_type = classify(endpoint)
    match endpoint_type:
        case Endpoint.GAMES:
            model_instance = model(name=form.get("name"), description=form.get("description"))
        case Endpoint.REGISTER:
            model_instance = User(
                email=form.get("email"),
                username=form.get("username"),
                password=Auth.get_password_hash(form.get("password")),
                role=form.get("role"),
                first_name=form.get("first_name"),
                last_name=form.get("last_name"),
                year_level=form.get("year_level"),
                house=form.get("house")
            )
        case _:
            return Response(status_code=status.HTTP_404_NOT_FOUND)
    try:
        await db.insert(session, model_instance)
    except IntegrityError:
        return Response(status_code=status.HTTP_409_CONFLICT)
    return RedirectResponse(f"/{endpoint}", status_code=status.HTTP_303_SEE_OTHER)


@app.patch("/{endpoint}/{identifier}", response_class=HTMLResponse)
async def update_record(request: Request, session: Session, identifier: int, endpoint: str):
    """
    Update game page
    TODO: Fix - adjust JS and create check to see which field was modified for the row.
    TODO: Utilise has_existed to return 410 Gone if record was deleted and existed, or 404 if it hasn't existed
    :param endpoint:
    :param identifier:
    :param request:
    :param session:
    :return:
    """
    # This code gets the form data from the request
    req_data: dict = await request.json()
    model, endpoint_type = classify(endpoint)
    if model is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    try:
        await db.update(session, model, identifier, req_data)
    except IntegrityError as e:
        print(e)
        return Response(status_code=status.HTTP_409_CONFLICT)
    except NoResultFound:
        if await db.has_existed(session, model, identifier):
            return Response(status_code=status.HTTP_410_GONE)
        else:
            return Response(status_code=status.HTTP_404_NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.delete("/{endpoint}/{identifier}", response_class=HTMLResponse)
async def delete_game(request: Request, session: Session, identifier: int, endpoint: str):
    """
    Route for game record deletion - does not check if the game exists before deletion
    :param endpoint:
    :param identifier:
    :param request:
    :param session:
    :return:
    """
    # This code gets the form data from the request
    form = await request.form()
    model, endpoint_type = classify(endpoint)
    print(form)
    await db.remove_record(session, model, identifier)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard(request: Request, session: Session):
    """
    Leaderboard page
    :param session:
    :param request:
    :return:
    """
    rankings = await db.dump_by_field_descending(session, models.MatchResult.won_id, "wins", 10)
    return templates.TemplateResponse(
        "leaderboard.html",
        {"request": request, "users": utils.get_users()},
    )


@app.get("/matches/{id}", response_class=HTMLResponse)
async def get_match(request: Request, match_id: int, session: Session):
    """
    :param session:
    :param request:
    :param match_id:
    :return:
    """
    try:
        match = await db.retrieve(session, models.Match, match_id)
    except NoResultFound:
        # TODO: adjust with a proper page regarding no match found with id
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return templates.TemplateResponse("matches.html", {"request": request, "id": match_id, "match": match})
