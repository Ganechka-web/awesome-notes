class BrokerError(Exception):
    def __init__(self, msg: str, *args):
        self.msg = msg
        super().__init__(*args)


class UnableToConnectToBrokerError(BrokerError):
    pass
