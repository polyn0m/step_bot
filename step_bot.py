import argparse
import logging
import os
import signal

from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv

from step_bot.bot import Bot

__version__ = '0.0.1'


def stop_signal(signum, frame):
    if bot:
        bot.stop()


def setup_logger():
    logger = logging.getLogger()

    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    request_access_log = getattr(logging, settings.LOG_LEVEL_REQUEST.upper())

    logger.setLevel(log_level)
    logging.getLogger("requests.packages.urllib3").level = request_access_log

    if settings.LOG_TO:
        handler = TimedRotatingFileHandler(settings.LOG_TO, when='midnight', backupCount=10)
        handler.setFormatter(logging.Formatter(
            '%(levelname)s - %(asctime)s: %(message)s', '%d.%m.%Y %H:%M:%S'
        ))

        logger.addHandler(handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Step Count Telegram Bot', description='%(prog)s it\'s counting steps for people'
    )

    parser.add_argument('-v', '--version', action='version', version=__version__)

    args = parser.parse_args()

    PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))

    d_filename = os.path.join(PROJECT_PATH, os.environ.get('DOTENV', '.env'))
    load_dotenv(d_filename)

    signal.signal(signal.SIGINT, stop_signal)
    signal.signal(signal.SIGHUP, stop_signal)
    signal.signal(signal.SIGTERM, stop_signal)

    from step_bot import settings

    setup_logger()

    bot = Bot(settings)
    bot.start()
