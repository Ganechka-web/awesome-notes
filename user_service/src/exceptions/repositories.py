class DataBaseError(Exception):
    def __init__(self, msg: str, *args):
        self.msg = msg
        super().__init__(*args)
