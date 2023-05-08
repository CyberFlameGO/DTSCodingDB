import sentry_sdk
from flask import Flask
from sentry_sdk.integrations.flask import FlaskIntegration
import utils

sentry_sdk.init(
    dsn = "https://eebca21dd9c9418cbfe83e7b8a0976de@o317122.ingest.sentry.io/4504873492480000",
    integrations = [
        FlaskIntegration(),
    ],
    send_default_pii = True,
    traces_sample_rate = 1.0,
    _experiments = {
        "profiles_sample_rate": 1.0,
    }
)

app = Flask(__name__)
db = utils.Database()


@app.route('/')
def hello_world():  # put application's code here
    """
    Displays a simple message to the user.
    :return:
    :rtype:
    """
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug = True)
