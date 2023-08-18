import fastapi
import sentry_sdk

import utils

sentry_sdk.init(
    dsn="https://eebca21dd9c9418cbfe83e7b8a0976de@o317122.ingest.sentry.io/4504873492480000",
    send_default_pii=True,
    traces_sample_rate=1.0,
    _experiments={
        "profiles_sample_rate": 1.0,
    },
)

app = fastapi.FastAPI()


# db = utils.Database() TODO: setup database tables and re-jig the spreadsheet layout


@app.get("/")
async def hello_world():  # put application's code here
    """
    Displays the homepage to the user
    :return:
    :rtype:
    """
    return flask.render_template("home.html")
