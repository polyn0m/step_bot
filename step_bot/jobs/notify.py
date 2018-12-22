import logging

import telegram

from step_bot.jobs import BotJob
from step_bot.models import Chat


class EveningReminder(BotJob):
    name = "evening_reminder"
    at = dict(
        hour=21
    )

    def execute(self):
        db_session = self.get_db()

        chats = db_session.query(Chat).all()

        for chat in chats:
            if chat.current_target_id:
                self.bot.send_message(
                    chat_id=chat.chat_id, text="А *ты* не забыл сдать показания шагов?!",
                    parse_mode=telegram.ParseMode.MARKDOWN
                )
