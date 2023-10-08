from typing import Annotated, AsyncGenerator, AsyncIterable, AsyncIterator

import sentry_sdk
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

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
session = Annotated[AsyncGenerator, Depends(db.get_session)]

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


@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard(request: Request):
    """
    Leaderboard page
    :param request:
    :return:
    """
    return templates.TemplateResponse(
        "leaderboard.html",
        {"request": request, "users": utils.get_users()},
    )


@app.get("/matches/{id}", response_class=HTMLResponse)
async def get_match(request: Request, match_id: str, session):
    """

    :param request:
    :param match_id:
    :return:
    """
    return templates.TemplateResponse("matches.html", {"request": request, "id": match_id})
