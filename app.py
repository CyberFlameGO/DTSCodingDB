from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Optional, Type

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

import models
import utils
from models import Base, Match, MatchPlayers, MatchResult, Token, User

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


class Endpoint(Enum):
    """
    Enum of endpoints
    """

    GAMES = "games"
    MATCH = "match"
    NEW_MATCH = "new_match"
    LOGIN = "login"
    REGISTER = "register"


class Roles(Enum):
    """
    Enum of roles
    """

    LEADER = "leader"
    STUDENT = "student"
    TEACHER = "teacher"


async def get_user(session, token: str):
    data = utils.get_authdata(token)
    user = await Auth.get_user_object(session, username=data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print(user)
    return user


def classify_endpoint(to_classify: Endpoint | str) -> tuple[Type[Base] | None, Endpoint | int]:
    """
    Abstracts endpoint classification away from route function
    These two are intentionally separated for annotation purposes and readability.
    The second parameter in the return (which is just be a tuple) is also intentionally there for readability
    :param to_classify:
    :return:
    """
    if to_classify in Endpoint:
        subject = Endpoint(to_classify)
    else:
        return None, status.HTTP_404_NOT_FOUND
    match subject:
        case Endpoint.GAMES:
            return models.Game, subject
        case Endpoint.LOGIN | Endpoint.REGISTER:
            return models.User, subject
        case Endpoint.MATCH | Endpoint.NEW_MATCH:
            return models.Match, subject
        case _:
            return None, status.HTTP_404_NOT_FOUND


def classify_role(to_classify: Roles | str):
    """
    Abstracts role classification away from route function.
    These two are intentionally separated for annotation purposes and readability.
    :param to_classify:
    :return:
    """
    if to_classify in Roles:
        subject = Roles(to_classify)
    else:
        return None, status.HTTP_404_NOT_FOUND
    match subject:
        case Roles.LEADER:
            return models.User, subject
        case Roles.STUDENT:
            return models.User, subject
        case Roles.TEACHER:
            return models.User, subject
        case _:
            return Roles.STUDENT


@app.on_event("startup")
async def startup():
    await db.connect()


@app.on_event("shutdown")
async def shutdown():
    pass


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session: Session):
    """
    Home page
    :param session:
    :param request:
    :return:
    """
    token = request.cookies.get("access_token")
    print(token)
    if token:
        val = await get_user(session, token)
        print(val.role)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


@app.post("/token", response_model=Token)
async def authenticate(
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
    access_token = Auth.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    response = RedirectResponse(url="/", status_code=status.HTTP_200_OK)
    response.set_cookie(
        key="access_token", value=access_token, expires=int(access_token_expires.total_seconds())
    )  # insecure but this program would need a
    # production context for a secure implementation (as in, one in mind for program design)
    return response


@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, session: Session):
    form = await request.form()
    new_user = User(
        email=form.get("email"),
        username=form.get("username"),
        password=Auth.get_password_hash(form.get("password")),
        role=form.get("role"),
        first_name=form.get("first_name"),
        last_name=form.get("last_name"),
        year_level=form.get("year_level"),
        house=form.get("house"),
    )
    try:
        await db.insert(session, new_user)
    except IntegrityError:
        return Response(status_code=status.HTTP_409_CONFLICT)
    return JSONResponse(content={"redirectUrl": "/"}, status_code=status.HTTP_303_SEE_OTHER)


@app.get("/auth_needed", response_class=HTMLResponse)
async def auth_needed(request: Request):
    """
    TODO: make httpexception thing go here
    Auth needed page
    :param request:
    :return:
    """
    return templates.TemplateResponse(
        "auth_needed.html",
        {
            "request": request,
        },
    )


@app.get("/match/{match_id}", response_class=HTMLResponse)
async def match(request: Request, session: Session, match_id: int):
    """
    Match page
    :param match_id:
    :param session:
    :param request:
    :return:
    """
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/auth_needed")
    user = await get_user(session, token)
    if match_id is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    row_stmt = (
        select(Match)
        .filter_by(id=match_id)
        .options(
            joinedload(Match.players).joinedload(MatchPlayers.player),
            joinedload(Match.results).joinedload(MatchResult.won),
        )
    )
    row = (await session.execute(row_stmt)).unique().scalar_one_or_none()
    games = await db.dump_all(session, models.Game)
    return templates.TemplateResponse(
        "match.html",
        {
            "request": request,
            "match": row.__dict__,
            "games": games,
            "editing_stick": True if user.role == Roles.TEACHER.value else False,
        },
    )


@app.get("/{endpoint}", response_class=HTMLResponse)
async def records_list(request: Request, session: Session, endpoint: str):
    """
    Games page
    :param endpoint:
    :param session:
    :param request:
    :return:
    """

    model, endpoint_type = classify_endpoint(endpoint)
    print(model, endpoint_type)

    token = request.cookies.get("access_token")
    if not token:
        if endpoint_type == Endpoint.LOGIN:
            return templates.TemplateResponse("login.html", {"request": request})
        elif endpoint_type == Endpoint.REGISTER:
            return templates.TemplateResponse("register.html", {"request": request})
        return RedirectResponse(url="/auth_needed")
    user = await get_user(session, token)

    if model is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    context: dict = {
        "request": request,
    }
    match endpoint_type:
        case Endpoint.GAMES:
            context["games"] = await db.dump_all(session, model)
            if user.role == Roles.TEACHER.value:
                context["editing_stick"] = True
        case Endpoint.NEW_MATCH:
            context["games"] = await db.dump_all(session, models.Game)
        case _:
            pass
    return templates.TemplateResponse(
        f"{endpoint_type.value}.html",
        context,
    )


@app.post("/{endpoint}", response_class=JSONResponse)
async def new_record(
    request: Request, session: Session, endpoint: str, token: Annotated[str, Depends(utils.oauth2_scheme)]
):
    """
    New game page
    :param user:
    :param token:
    :param endpoint:
    :param request:
    :param session:
    :return:
    """

    user = await get_user(session, token)
    form = await request.form()
    print(form)
    model, endpoint_type = classify_endpoint(endpoint)
    match endpoint_type:
        case Endpoint.GAMES:
            if user.role != Roles.TEACHER.value:
                return Response(status_code=status.HTTP_403_FORBIDDEN)
            model_instance = model(name=form.get("name"), description=form.get("description"))
        case Endpoint.MATCH:
            print("match")
            winner = await db.retrieve_by_field(session, User, User.username, form.get("winner"))
            loser = await db.retrieve_by_field(session, User, User.username, form.get("loser"))
            played_at = None
            if form.get("played_at"):
                played_at = datetime.strptime(form.get("played_at"), "%Y-%m-%dT%H:%M")
            print(form.get("game"), user.id, played_at, winner.id, loser.id)
            model_instance = model(
                game_id=form.get("game"),
                creator_id=user.id,  # TODO: get user id from token
                played_at=played_at,
                players={
                    MatchPlayers(
                        player_id=winner.id,
                    ),
                    MatchPlayers(player_id=loser.id),
                },
                results=MatchResult(won_id=winner.id, lost_id=loser.id),
            )
            print(model.__dict__)

        case _:
            return Response(status_code=status.HTTP_404_NOT_FOUND)
    try:
        await db.insert(session, model_instance)
    except IntegrityError:
        return Response(status_code=status.HTTP_409_CONFLICT)
    if endpoint_type == Endpoint.MATCH:
        return JSONResponse(
            content={"redirectUrl": f"/{endpoint_type.value}?identifier={model_instance.id}"},
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return JSONResponse(content={"redirectUrl": f"/{endpoint_type.value}"}, status_code=status.HTTP_303_SEE_OTHER)


@app.patch("/{endpoint}/{identifier}", response_class=Response)
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
    model, endpoint_type = classify_endpoint(endpoint)
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


@app.delete("/{endpoint}/{identifier}", response_class=Response)
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
    model, endpoint_type = classify_endpoint(endpoint)
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0")
