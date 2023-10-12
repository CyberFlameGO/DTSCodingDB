from typing import Annotated, AsyncGenerator, AsyncIterable, AsyncIterator

import uvicorn

import sentry_sdk
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

import models
import utils
from utils import Database

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


@app.get("/games", response_class=HTMLResponse)
async def games_list(request: Request, session: Session):
    """
    Games page
    :param session:
    :param request:
    :return:
    """
    games = await db.dump_all(session, models.Game)
    return templates.TemplateResponse(
        "games.html",
        {
            "request": request,
            "games": games,
            "can_mutate_games": True,
        },
    )


@app.post("/games", response_class=HTMLResponse)
async def new_game(request: Request, session: Session):
    """
    New game page
    :param request:
    :param session:
    :return:
    """
    # This code gets the form data from the request
    form = await request.form()
    print(form)
    game = models.Game(name=form.get("name"), description=form.get("description"))
    await db.insert(session, game)
    return RedirectResponse("/games", status_code=303)


@app.patch("/games/{id}", response_class=HTMLResponse)
async def update_game(request: Request, session: Session):
    """
    Update game page
    TODO: Fix - adjust JS and create check to see which field was modified for the row.
    :param request:
    :param session:
    :return:
    """
    # This code gets the form data from the request
    form = await request.form()
    print(form)
    game = await db.retrieve(session, models.Game, int(form.get("id")))
    game.name = form.get("name")
    game.description = form.get("description")
    await db.update(
        session, models.Game, int(form.get("id")), {"name": form.get("name"), "description": form.get("description")}
    )
    return RedirectResponse("/games", status_code=303)


@app.delete("/games", response_class=HTMLResponse)
async def delete_game(request: Request, session: Session):
    """
    Delete game page
    :param request:
    :param session:
    :return:
    """
    # This code gets the form data from the request
    form = await request.form()
    print(form)
    await db.delete(session, models.Game, int(form.get("id")))
    return RedirectResponse("/games", status_code=303)


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
