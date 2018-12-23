import logging
from datetime import datetime

import telegram
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from step_bot.jobs import BotJob
from step_bot.models import Chat, Step


class EveningReminder(BotJob):
    name = "evening_reminder"
    at = dict(
        hour=21
    )

    def execute(self):
        db_session = self.get_db()

        chats = db_session.query(Chat).outerjoin(Chat.current_target) \
                .all()

        for chat in chats:
            if chat.current_target and not chat.is_target_complete():
                self.bot.send_message(
                    chat_id=chat.chat_id, text="А *ты* не забыл сдать показания шагов?!",
                    parse_mode=telegram.ParseMode.MARKDOWN
                )


class EveningStat(BotJob):
    name = "evening_stat"
    at = dict(
        hour=23,
        minute=55
    )

    def execute(self):
        db_session = self.get_db()

        chats = db_session.query(Chat).outerjoin(Chat.current_target) \
            .all()

        today = datetime.now(tz=self.settings.BOT_TZ).date()

        for chat in chats:
            if chat.current_target and not chat.is_target_complete():
                steps = 0

                try:
                    aggregate = db_session.query(func.sum(Step.steps).label('today'))\
                        .filter(
                            Step.target == chat.current_target,
                            Step.date == today
                        )\
                        .group_by(Step.target_id)\
                        .one()
                    steps = aggregate.today
                except NoResultFound:
                    pass
                finally:
                    self.bot.send_message(
                        chat_id=chat.chat_id, text="День подходит к концу и сегодня мы прошли *{0:.2f} км*".format(
                            steps / 1000
                        ),
                        parse_mode=telegram.ParseMode.MARKDOWN
                    )
