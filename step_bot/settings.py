import os


def environ_var(key, default=None):
    val = os.environ.get(key, default)
    if val == 'True':
        return True
    elif val == 'False':
        return False
    return val


globals().update(os.environ)

DEBUG = environ_var("DEBUG", True)

BOT_TOKEN = environ_var("BOT_TOKEN", '')
BOT_PROXY_ENABLE = environ_var("DEBUG", False)
BOT_REQUEST_KWARGS = dict()

if BOT_PROXY_ENABLE:
    BOT_REQUEST_KWARGS.update(dict(
        proxy_url=environ_var("BOT_PROXY_URL", ''),
        urllib3_proxy_kwargs=dict(
            username=environ_var("BOT_PROXY_USER", ''),
            password=environ_var("BOT_PROXY_PASSWORD", '')
        )
    ))

LOG_TO = environ_var("LOG_TO", '')

LOG_LEVEL = environ_var("LOG_LEVEL", 'info')
LOG_LEVEL_ACCESS = environ_var("LOG_LEVEL_ACCESS", 'error')
LOG_LEVEL_REQUEST = environ_var("LOG_LEVEL_REQUEST", 'error')

POSTGRES_DB = environ_var("POSTGRES_DB", 'step_bot')
POSTGRES_HOST = environ_var("POSTGRES_HOST", 'localhost')
POSTGRES_PORT = int(environ_var("POSTGRES_PORT", 5432))
POSTGRES_USER = environ_var("POSTGRES_USER", 'step_bot_user')
POSTGRES_PASS = environ_var("POSTGRES_PASS", 'step_bot_pass')
POSTGRES_MAX_CONN = int(environ_var("POSTGRES_MAX_CONN", 2))
