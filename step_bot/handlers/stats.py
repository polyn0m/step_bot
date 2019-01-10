import logging
import textwrap

import telegram
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from step_bot.handlers import CommandBaseHandler, CheckTargetMixin
from step_bot.models import Chat, Step


class StatHandler(CommandBaseHandler, CheckTargetMixin):
    command = "stat"

    def clean_args(self, args):
        return dict()

    def execute(self, bot, update, cleaned_args):
        chat_id = update.effective_chat.id

        db_session = self.get_db()

        try:
            current_chat = db_session.query(Chat).outerjoin(Chat.current_target) \
                .filter(Chat.chat_id == str(chat_id)) \
                .one()

            if not self.have_target(bot, current_chat):
                return

            user_steps = 0
            try:
                aggregate = db_session.query(func.sum(Step.steps).label('user_steps')) \
                    .filter(
                        Step.user_id == str(update.message.from_user.id),
                        Step.target_id == current_chat.current_target_id
                    ) \
                    .group_by(Step.target_id) \
                    .one()
                user_steps = aggregate.user_steps
            except NoResultFound:
                pass

            name = current_chat.current_target.name
            target = current_chat.current_target.target_value / 1000
            now = current_chat.current_target.current_value / 1000
            end_date = current_chat.current_target.target_date.strftime("%d.%m.%Y")
            percent = now / target * 100

            bot.send_message(
                chat_id=chat_id, text=textwrap.dedent("""\
                Наша цель *{0}* в *{1} км* к *{2}*
                На данный момент мы прошли: *{3} км* (*{4:.2f}%* от цели)
                
                Твой вклад в эту цель составляет *{5} км*!
                """.format(name, target, end_date, now, percent, user_steps / 1000)),
                reply_to_message_id=update.effective_message.message_id, parse_mode=telegram.ParseMode.MARKDOWN)
        except NoResultFound as e:
            self.send_error(bot, chat_id, reply_to_message_id=update.effective_message.message_id)

            logging.exception(e)
        finally:
            db_session.commit()
