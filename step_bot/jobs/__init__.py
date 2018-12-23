from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

jobs = dict()


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
        jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=settings.BOT_TZ
    )

    return scheduler, init_jobs(scheduler, bot, db, settings)


def init_jobs(scheduler, bot, db, settings):
    from step_bot.jobs.notify import EveningReminder, EveningStat

    options = dict(scheduler=scheduler, bot=bot, db=db, settings=settings)

    evening_reminder = EveningReminder(**options)
    evening_stat = EveningStat(**options)

    jobs[evening_reminder.name] = evening_reminder
    jobs[evening_stat.name] = evening_stat

    return jobs


def execute_job(job_name):
    job = jobs[job_name]

    job.execute()


class BotJob:
    settings = None

    name = ""
    at = dict()

    job = None

    bot = None
    get_db = None

    def __init__(self, scheduler, bot, db, settings):
        self.settings = settings

        self.bot = bot
        self.get_db = db

        self.job = scheduler.add_job(
            execute_job, 'cron', **self.at, id=self.name, kwargs=dict(job_name=self.name), replace_existing=True
        )

    def execute(self):
        NotImplemented("It is abstract job!")
