class SentinelError(Exception):
    pass

class DecodingError(SentinelError):
    pass

class ProcessingError(SentinelError):
    pass
