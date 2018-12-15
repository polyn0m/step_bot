class BaseHandler:
    dispatcher = None
    db = None

    def __init__(self, dispatcher, db):
        self.dispatcher = dispatcher
        self.get_db = db
