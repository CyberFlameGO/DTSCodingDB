from enum import Enum
from typing import Annotated, Type

import sentry_sdk
from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

import models
import utils

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
Session = Annotated[AsyncSession, Depends(db.get_session)]

# TODO: adapt the following:


class Endpoint(Enum):
    """
    Enum of endpoints
    """
    GAMES = "games"


def classify(to_classify: Endpoint | str) -> Type[models.Base] | None:
    """
    Abstracts endpoint classification away from route function
    :param to_classify:
    :return:
    """
    match to_classify:
        case Endpoint.GAMES:
            return models.Game
        case _:
            return None


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
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


@app.get("/{endpoint}", response_class=HTMLResponse)
async def records_list(request: Request, session: Session, endpoint: str | Endpoint):
    """
    Games page
    :param endpoint:
    :param session:
    :param request:
    :return:
    """
    model = classify(Endpoint(endpoint))
    if model is None:
        return Response(status_code = status.HTTP_404_NOT_FOUND)

    return templates.TemplateResponse(
        "games.html",
        {
            "request": request,
            "data": await db.dump_all(session, model),
            "can_mutate_games": True,
        },
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
    match endpoint:  # match-case, not 'match' as in the object
        case "games":
            model = models.Game(name=form.get("name"), description=form.get("description"))
        case _:
            return Response(status_code=status.HTTP_404_NOT_FOUND)
    try:
        await db.insert(session, model)
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
    model = classify(endpoint)
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
    model = classify(endpoint)
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
    match = await db.retrieve(session, models.Match, match_id)
    return templates.TemplateResponse("matches.html", {"request": request, "id": match_id, "match": match})
