import logging
import textwrap

import telegram
from sqlalchemy.orm.exc import NoResultFound

from step_bot.handlers import CommandBaseHandler, CheckTargetMixin
from step_bot.models import Chat


class StatHandler(CommandBaseHandler, CheckTargetMixin):
    command = "stat"

    def clean(self, args):
        return dict()

    def execute(self, bot, update, cleaned_args):
        db_session = self.get_db()

        try:
            chat_id = update.message.chat_id

            current_chat = db_session.query(Chat).outerjoin(Chat.current_target) \
                .filter(Chat.chat_id == str(chat_id)) \
                .one()

            if not self.have_target(bot, current_chat):
                return

            name = current_chat.current_target.name
            target = current_chat.current_target.target_value / 1000
            now = current_chat.current_target.current_value / 1000
            end_date = current_chat.current_target.target_date.strftime("%d.%m.%Y")
            percent = now / target * 100

            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
                Наша цель *{0}* в *{1} км* к *{2}*
                На данный момент мы прошли: *{3} км* (*{4:.2f}%* от цели)
                """.format(name, target, end_date, now, percent)), parse_mode=telegram.ParseMode.MARKDOWN)
        except NoResultFound as e:
            self.send_error(bot, update.message.chat_id)
            logging.exception(e)
        finally:
            db_session.commit()
