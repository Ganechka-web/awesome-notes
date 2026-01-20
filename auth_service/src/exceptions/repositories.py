from src.exceptions.base import AuthServiceException

class RepositoryError(AuthServiceException):
    pass 

class DataBaseError(RepositoryError):
    pass


class RowDoesNotExist(DataBaseError):
    pass


class RowAlreadyExists(DataBaseError):
    pass


class TokenDoesNotExists(RepositoryError):
    pass