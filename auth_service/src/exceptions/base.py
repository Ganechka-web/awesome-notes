class AuthServiceException(Exception):
    def __init__(self, msg: str, *args) -> None:
        self.msg = msg
        super().__init__(msg, *args)
