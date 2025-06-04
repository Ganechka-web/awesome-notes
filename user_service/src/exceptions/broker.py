class BrokerError(Exception):
    def __init__(self, msg: str, *args):
        self.msg = msg
        super().__init__(*args)


class PublisherCantConnectToBrokerError(BrokerError):
    """Raises when get_connection_to_broker returns None"""
    pass
