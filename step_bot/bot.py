import logging

from telegram.ext import Updater
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from step_bot.handlers.greetings import GroupHandler, P2PEchoHandler
from step_bot.models import Base


class Bot:
    settings = None

    handlers = set()

    db_engine = None
    get_db = None

    def __init__(self, settings):
        logging.info('Step Count Bot initialization...')

        self.settings = settings

        self.updater = Updater(self.settings.BOT_TOKEN, request_kwargs=self.settings.BOT_REQUEST_KWARGS)

        self.init_database()
        self.init_handlers()

    def init_database(self):
        self.db_engine = create_engine(
            "postgresql+psycopg2://{login}:{password}@{host}:{port}/{database}".format(
                login=self.settings.POSTGRES_USER, password=self.settings.POSTGRES_PASS,
                host=self.settings.POSTGRES_HOST, port=self.settings.POSTGRES_PORT,
                database=self.settings.POSTGRES_DB
            ), echo=True
        )

        self.get_db = sessionmaker(bind=self.db_engine)

        Base.metadata.create_all(self.db_engine)

    def init_handlers(self):
        options = dict(
            dispatcher=self.updater.dispatcher,
            db=self.get_db
        )

        self.handlers.add(P2PEchoHandler(**options))

        self.handlers.add(GroupHandler(**options))

    def start(self):
        logging.info('Starting pooling...')

        self.updater.start_polling()

    def stop(self):
        logging.info('Stopping pooling...')

        self.updater.stop()
