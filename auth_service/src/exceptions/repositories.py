from exceptions.base import AuthServiceException


class DataBaseError(AuthServiceException):
    pass


class RowDoesNotExist(DataBaseError):
    pass


class RowAlreadyExists(DataBaseError):
    pass
