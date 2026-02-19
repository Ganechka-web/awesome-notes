class ServiceError(Exception):
    def __init__(self, msg: str, *args):
        self.msg = msg
        super().__init__(msg, *args)


class NoteNotFoundError(ServiceError):
    pass


class NoteAlreadyExistsError(ServiceError):
    pass
