from exceptions.base import AuthServiceException


class ServiceError(AuthServiceException):
    pass


class AuthCredentialsNotFoundError(ServiceError):
    pass


class AuthCredentialsAlreadyExistsError(ServiceError):
    pass


class PasswordsDidNotMatch(ServiceError):
    pass


class UnableToCreareAuthCredentials(ServiceError):
    """Raises when broker can`t created user id, or broker is unavailable"""

    pass
