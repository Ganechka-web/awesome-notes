from src.exceptions.base import AuthServiceException


class BrokerError(AuthServiceException):
    pass


class UnableToConnectToBrokerError(BrokerError):
    pass


class ReceivingResponseTimeOutError(BrokerError):
    """Raises when RPC client was waiting for response too long"""
