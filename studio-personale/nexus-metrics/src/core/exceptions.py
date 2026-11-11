class RiotAPIError(Exception):
    pass

class RateLimitExceededError(RiotAPIError):
    pass

class PlayerNotFoundError(RiotAPIError):
    pass