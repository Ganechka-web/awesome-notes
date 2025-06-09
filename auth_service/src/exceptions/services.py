from exceptions.base import AuthServiceException


class ServiceError(AuthServiceException):
    pass


class AuthCredentialsNotFoundError(ServiceError):
    pass


class AuthCredentialsAlreadyExistsError(ServiceError):
    pass


class PasswordsDidNotMatch(ServiceError):
    pass
