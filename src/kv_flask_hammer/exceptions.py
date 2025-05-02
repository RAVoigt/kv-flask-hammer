
class FlaskHammerError(Exception):
    pass


class AlreadyStartedError(FlaskHammerError):
    pass

class ImmutableConfigError(AlreadyStartedError):
    pass
