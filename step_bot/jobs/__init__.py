from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc


def init_scheduler(settings, bot, db):
    scheduler = BackgroundScheduler()

    jobstores = dict(
        default=SQLAlchemyJobStore(
            url="postgresql+psycopg2://{login}:{password}@{host}:{port}/{database}".format(
                login=settings.POSTGRES_USER, password=settings.POSTGRES_PASS,
                host=settings.POSTGRES_HOST, port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DB
            )
        )
    )
    job_defaults = dict(coalesce=False, max_instances=3)
    executors = dict(default=dict(type="threadpool", max_workers=5))

    scheduler.configure(
        jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc
    )

    return scheduler, init_jobs(scheduler, bot, db)


def init_jobs(scheduler, bot, db):
    return set()


class BotJob:
    bot = None
    db = None

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
