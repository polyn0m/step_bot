import logging

from telegram.ext import Updater
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from step_bot.handlers import init_handlers
from step_bot.jobs import init_scheduler
from step_bot.models import Base


class Bot:
    settings = None

    updater = None
    handlers = set()

    scheduler = None
    jobs = set()

    db_engine = None
    get_db = None

    def __init__(self, settings):
        logging.info('Step Count Bot initialization...')

        self.settings = settings

        self.init_database()

        self.init_updater()
        self.init_scheduler()

    def init_updater(self):
        self.updater = Updater(self.settings.BOT_TOKEN, request_kwargs=self.settings.BOT_REQUEST_KWARGS)

        options = dict(
            dispatcher=self.updater.dispatcher,
            db=self.get_db
        )

        self.handlers = init_handlers(**options)

    def init_database(self):
        self.db_engine = create_engine(
            "postgresql+psycopg2://{login}:{password}@{host}:{port}/{database}".format(
                login=self.settings.POSTGRES_USER, password=self.settings.POSTGRES_PASS,
                host=self.settings.POSTGRES_HOST, port=self.settings.POSTGRES_PORT,
                database=self.settings.POSTGRES_DB
            )
        )

        self.get_db = sessionmaker(bind=self.db_engine)

        Base.metadata.create_all(self.db_engine)

    def init_scheduler(self):
        options = dict(
            settings=self.settings,
            bot=self.updater.bot,
            db=self.get_db
        )

        self.scheduler, self.jobs = init_scheduler(**options)

    def start(self):
        logging.info('Starting bot...')

        self.updater.start_polling()
        self.scheduler.start()

    def stop(self):
        logging.info('Stopping bot...')

        self.scheduler.shutdown()
        self.updater.stop()
