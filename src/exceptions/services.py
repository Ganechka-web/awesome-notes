class ServiceError(Exception):
    def __init__(self, msg: str, *args):
        self.msg = msg
        super().__init__(*args)


class UserNotFoundError(ServiceError):
    pass


class UserAlreadyExistsError(ServiceError):
    pass
