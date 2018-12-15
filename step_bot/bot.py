import logging

from telegram.ext import Updater


class Bot:
    def __init__(self, settings):
        logging.info('Step Count Bot initialization...')

        self.updater = Updater(settings.BOT_TOKEN, request_kwargs=settings.BOT_REQUEST_KWARGS)

    def start(self):
        logging.info('Starting pooling...')

        self.updater.start_polling()

    def stop(self):
        logging.info('Stopping pooling...')

        self.updater.stop()
