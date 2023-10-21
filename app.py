from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Type

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, join
from sqlalchemy.orm import joinedload

import models
import utils
from models import Base, Game, Match, MatchPlayers, MatchResult, Token, User, UserInDB

sentry_sdk.init(
    dsn="https://eebca21dd9c9418cbfe83e7b8a0976de@o317122.ingest.sentry.io/4504873492480000",
    send_default_pii=True,
    traces_sample_rate=1.0,
    _experiments={
        "profiles_sample_rate": 1.0,
    },
)  # Sets up error monitoring - helps with tracking errors

templates = Jinja2Templates(directory="templates")  # Sets the template directory for Jinja2 templates
app = FastAPI()  # Sets the FastAPI app
app.mount("/static", StaticFiles(directory="static"), name="static")  # Sets the static directory (for CSS/JS)

db = utils.Database("data.db")  # Create an instance of the database object

Auth = utils.Auth  # Alias Auth to the utils.Auth class without instance creation
Session = Annotated[AsyncSession, Depends(db.get_session)]  # Annotation for dependency injection


# Enum classes
class Endpoint(Enum):
    """
    Enum of endpoints
    """

    GAMES = "games"
    MATCH = "match"
    NEW_MATCH = "new_match"
    LOGIN = "login"
    REGISTER = "register"
    LEADERBOARD = "leaderboard"


class Roles(Enum):
    """
    Enum of roles
    """

    LEADER = "leader"
    STUDENT = "student"
    TEACHER = "teacher"


async def get_user(session, token: str) -> UserInDB:
    """
    Asynchronous function to validate credentials.
    On successful validation, returns Pydantic model.

    :param session:
    :param token:
    :return:
    """
    data = utils.get_authdata(token)
    user = await Auth.get_user_object(session, username=data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Identify values where necessary for role and endpoint
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
    """
    Deprecated (emits warning) method of invoking code on ASGI startup.
    It sets variables but notably creates metadata.
    The method being called may not appear necessary as its own method, as in it may appear better suited to the
    __init__ method, but __init__ cannot be async, and the engine needs to be awaited (even to synchronously create
    metadata).
    """
    await db.connect()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session: Session):
    """
    Home page
    :param session:
    :param request:
    :return:
    """
    token = request.cookies.get("access_token")  # Get the access token from the cookie
    # These start as None to avoid errors
    user = None
    user_total_plays = None
    user_total_wins = None
    if token:
        try:
            user = await get_user(session, token)  # tries to get user
            # gets user stats
            user_total_plays = (
                await session.execute(
                    select(func.count(MatchPlayers.match_id))
                    .join(Match, Match.id == MatchPlayers.match_id)
                    .where(MatchPlayers.player_id == user.id)
                )
            ).scalar_one_or_none()
            user_total_wins = (
                await session.execute(select(func.count(MatchResult.won_id)).where(MatchResult.won_id == user.id))
            ).scalar_one_or_none()
        except HTTPException:
            pass  # ignored since this is index page

    # Gets match count per game
    game_plays = (
        await session.execute(
            select(Game.name, func.count(Match.game_id).label("matches"))
            .select_from(join(Match, Game, Match.game_id == Game.id))
            .group_by(Game.name)
            .order_by(func.count(Match.game_id).desc())
        )
    ).all()
    # Returns it all to the template - request is a required context variable
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "game_plays": game_plays,
            "user_total_plays": user_total_plays,
            "user_total_wins": user_total_wins,
            "user": user,
        },
    )


@app.post("/token", response_model=Token)
async def authenticate(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session,
):
    """
    Route for authentication - adapted from FastAPI docs
    Adapted from https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
    :param form_data:
    :param session:
    :return:
    """
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
    """
    Route for registration - separated to not need authentication
    :param request:
    :param session:
    :return:
    """
    # Gets form values
    form = await request.form()
    # Puts the values through the SQLAlchemy model
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
    # Tries to insert the user into the database
    try:
        await db.insert(session, new_user)
    except IntegrityError:
        # If there is a conflicting entry, return a 409 Conflict
        return Response(status_code=status.HTTP_409_CONFLICT)
    # If successful, specify to JS that the user should be redirected to the home page
    return JSONResponse(content={"redirectUrl": "/"}, status_code=status.HTTP_303_SEE_OTHER)


@app.get("/auth_needed", response_class=HTMLResponse)
async def auth_needed(request: Request):
    """
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
    Match route - separated for readability
    :param match_id:
    :param session:
    :param request:
    :return:
    """

    token = request.cookies.get("access_token")  # Gets the access token from the cookie
    if not token:
        # If there is no access token, redirect to auth_needed
        return RedirectResponse(url="/auth_needed")
    # Gets the user from the token - no error handling necessary
    user = await get_user(session, token)
    if match_id is None:
        # If there is no match ID, return a 404
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    # Query for the match including related data
    row_stmt = (
        select(Match)
        .filter_by(id=match_id)
        .options(
            joinedload(Match.players).joinedload(MatchPlayers.player),
            joinedload(Match.results).joinedload(MatchResult.won),
        )
    )
    # Execute the query and get the first result
    row = (await session.execute(row_stmt)).unique().scalar_one_or_none()
    if row is None:
        # If there is no match, return a 404
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    # Get the game from the match
    try:
        game = await db.retrieve(session, models.Game, row.game_id)
    except NoResultFound:
        # If there is no game (if it's deleted), return a 404
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    # Get all games for the dropdown
    return templates.TemplateResponse(
        "match.html",
        {
            "request": request,
            "match": row.__dict__,
            "game_name": game.name,
            "editing_stick": True if user.role == Roles.TEACHER.value else False,
        },
    )


@app.get("/leaderboard", response_class=HTMLResponse)
async def get_leaderboard(request: Request, session: Session):
    """
    Leaderboard page
    :param session:
    :param request:
    :return:
    """
    # Queries the database for data needed
    leaderboard = await db.dump_by_field_descending(session, MatchResult.won_id, "wins")
    leaderboard_data = []  # Empty list to store data
    # Iterates through the leaderboard data and gets the username for each user
    for user_won_id, wins in leaderboard:
        select_statement = select(User.username).where(User.id == user_won_id)
        result = await session.execute(select_statement)
        username = result.scalars().first()
        leaderboard_data.append({"user": username, "wins": wins})
    # Returns the data to the template
    return templates.TemplateResponse(
        "leaderboard.html",
        {"request": request, "data": leaderboard_data},
    )


@app.get("/{endpoint}", response_class=HTMLResponse)
async def records_list(request: Request, session: Session, endpoint: str):
    """
    Handles most GET requests
    :param endpoint:
    :param session:
    :param request:
    :return:
    """
    # Classifies the endpoint, and the database model to use
    model, endpoint_type = classify_endpoint(endpoint)

    # If the endpoint is login or register, return the template, skipping auth requirement
    if endpoint_type == Endpoint.LOGIN:
        return templates.TemplateResponse("login.html", {"request": request})
    elif endpoint_type == Endpoint.REGISTER:
        return templates.TemplateResponse("register.html", {"request": request})

    # Gets the access token from the cookie
    token = request.cookies.get("access_token")
    # If there is no access token, redirect to auth_needed
    if not token:
        return RedirectResponse(url="/auth_needed")
    # Gets the user from the token - no error handling necessary
    user = await get_user(session, token)

    # If the model is None (which occurs when the endpoint isn't classified), return a 404
    if model is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # Creates the context dictionary
    context: dict = {
        "request": request,
    }
    # Gets the data from the database where applicable
    match endpoint_type:
        case Endpoint.GAMES:
            # Gets all games
            context["games"] = await db.dump_all(session, model)
            if user.role == Roles.TEACHER.value:  # If the user is a teacher, they can edit games
                context["editing_stick"] = True
        case Endpoint.NEW_MATCH:
            # If the user is not a teacher/leader, redirect to auth_needed (instead of returning 403, so the user sees a
            # cleaner page)
            if user.role != Roles.TEACHER.value and user.role != Roles.LEADER.value:
                return RedirectResponse(url="/auth_needed", status_code=status.HTTP_303_SEE_OTHER)
            # Gets all games for the dropdown
            context["games"] = await db.dump_all(session, models.Game)
        case _:
            pass
    # Returns the template
    return templates.TemplateResponse(
        f"{endpoint_type.value}.html",
        context,
    )


@app.post("/{endpoint}", response_class=JSONResponse)
async def new_record(
    request: Request, session: Session, endpoint: str, token: Annotated[str, Depends(utils.oauth2_scheme)]
):
    """
    Handles most POST requests, uses header for authentication
    :param token:
    :param endpoint:
    :param request:
    :param session:
    :return:
    """

    # Gets the user from the token - no error handling necessary
    user = await get_user(session, token)
    form = await request.form()  # Gets the form data
    # Classifies the endpoint, and the database model to use
    model, endpoint_type = classify_endpoint(endpoint)
    # Determines where the request came from and what to run
    match endpoint_type:
        case Endpoint.GAMES:
            # If the user is not a teacher, return a 403 Forbidden
            if user.role != Roles.TEACHER.value:
                return Response(status_code=status.HTTP_403_FORBIDDEN)
            # Creates the model instance with form data
            model_instance = model(name=form.get("name"), description=form.get("description"))
        case Endpoint.MATCH:
            # If the user is not a teacher nor student leader, return a 403 Forbidden
            if user.role != Roles.TEACHER.value and user.role != Roles.LEADER.value:
                return Response(status_code=status.HTTP_403_FORBIDDEN)
            # Gets the winner and loser from the form data
            winner = await db.retrieve_by_field(session, User, User.username, form.get("winner"))
            loser = await db.retrieve_by_field(session, User, User.username, form.get("loser"))
            # If the user specifies time/date, parse it
            played_at = None
            if form.get("played_at"):
                played_at = datetime.strptime(form.get("played_at"), "%Y-%m-%dT%H:%M")
            # Creates the model instance with form data
            model_instance = model(
                game_id=form.get("game"),
                creator_id=user.id,
                played_at=played_at,
                players={
                    MatchPlayers(
                        player_id=winner.id,
                    ),
                    MatchPlayers(player_id=loser.id),
                },
                results=MatchResult(won_id=winner.id, lost_id=loser.id),
            )
        case _:
            # If the endpoint isn't identified, return a 404
            return Response(status_code=status.HTTP_404_NOT_FOUND)
    # Tries to insert the model instance into the database
    try:
        new_record_id = await db.insert(session, model_instance)
    except IntegrityError:
        # If there is a conflicting entry, return a 409 Conflict
        return Response(status_code=status.HTTP_409_CONFLICT)
    if endpoint_type == Endpoint.MATCH:
        # If the endpoint is a match, return a redirect to the new match's page
        return JSONResponse(
            content={"redirectUrl": f"/{endpoint_type.value}/{new_record_id}"},
            status_code=status.HTTP_303_SEE_OTHER,
        )
    # If the endpoint is not a match, return a redirect to the endpoint's page (refresh)
    return JSONResponse(content={"redirectUrl": f"/{endpoint_type.value}"}, status_code=status.HTTP_303_SEE_OTHER)


@app.patch("/{endpoint}/{identifier}", response_class=Response)
async def update_record(
    request: Request,
    session: Session,
    identifier: int,
    endpoint: str,
    token: Annotated[str, Depends(utils.oauth2_scheme)],
):
    """
    Update record route - uses header for authentication
    :param token:
    :param endpoint:
    :param identifier:
    :param request:
    :param session:
    :return:
    """
    # Gets the user from the token - no error handling necessary
    user = await get_user(session, token)
    # If the user is not a teacher, return a 403 Forbidden
    if user.role != Roles.TEACHER.value:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    # This code gets the form data from the request
    req_data: dict = await request.json()

    # Classifies the endpoint, and the database model to use
    model, endpoint_type = classify_endpoint(endpoint)
    # If the model is None (which occurs when the endpoint isn't classified), return a 404
    if model is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    # Tries to update the record
    try:
        await db.update(session, model, identifier, req_data)
    except IntegrityError:
        # If there is a conflicting entry, return a 409 Conflict
        return Response(status_code=status.HTTP_409_CONFLICT)
    except NoResultFound:
        # If there is no result found, return a 410 if it could've existed in the past, otherwise a 404
        if await db.has_existed(session, model, identifier):
            return Response(status_code=status.HTTP_410_GONE)
        else:
            return Response(status_code=status.HTTP_404_NOT_FOUND)
    # If successful, return a 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.delete("/{endpoint}/{identifier}", response_class=Response)
async def delete_record(
    request: Request,
    session: Session,
    identifier: int,
    endpoint: str,
    token: Annotated[str, Depends(utils.oauth2_scheme)],
):
    """
    Route for game record deletion - does not check for existence before deletion
    Uses header for authentication
    :param token:
    :param endpoint:
    :param identifier:
    :param request:
    :param session:
    :return:
    """
    # Gets the user from the token - no error handling necessary
    user = await get_user(session, token)
    # If the user is not a teacher, return a 403 Forbidden
    if user.role != Roles.TEACHER.value:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    # Gets the form data from the request
    form = await request.form()
    model, endpoint_type = classify_endpoint(endpoint)  # Classifies the endpoint, and the database model to use
    if model is None:
        # If the model is None (which occurs when the endpoint isn't classified), return a 404
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    # Remove the record
    await db.remove_record(session, model, identifier)
    # Return a 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)
