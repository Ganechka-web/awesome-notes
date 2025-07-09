from exceptions.base import AuthServiceException


class PublisherCantConnectToBrokerError(AuthServiceException):
    """Raises when get_connection_to_broker returns None"""


class PublisherTimeoutReceivingResponseError(AuthServiceException):
    """Raises when publisher was waiting for response too long"""
