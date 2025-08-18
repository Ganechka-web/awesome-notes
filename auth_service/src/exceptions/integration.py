from exceptions.base import AuthServiceException


class ServiceIntegrationException(AuthServiceException):
    def __init__(self, msg: str, http_status_code: int, msg_from_service: str) -> None:
        """
        ServiceIntegrationError is an exception class for managing exceptions from the others services

        http_status_code - parameter for error's status code\n
        msg_from_service - for original error message from service
        """
        self.http_status_code = http_status_code
        self.msg_from_service = msg_from_service
        super().__init__(msg)


class UserServiceIntegrationException(ServiceIntegrationException):
    """Base class for integration with user_service exceptions"""


class UserCreationException(UserServiceIntegrationException):
    """Exception for user creation errors from user_service"""
