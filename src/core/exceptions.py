"""
Global exception and warning classes.
"""


class MatchaException(Exception):
    code = 500

    @property
    def message(self):
        return self.args[0]


class InvalidUsage(MatchaException):
    def __init__(self, message, status_code=400):
        super().__init__(self, message)
        self.status_code = status_code
        self.code = status_code

    def to_dict(self):
        rv = {'message': self.message}
        return rv


class ImproperlyConfigured(MatchaException):
    """
    App is somehow improperly configured
    """
    pass


# usage not found
class MethodError(MatchaException):
    code = 400


class ArgumentError(MatchaException):
    code = 400


class DishError(MatchaException):
    code = 400


class WineMenuError(MatchaException):
    code = 400


class WinePropertyError(MatchaException):
    pass


class WineNotFoundError(MatchaException):
    code = 404


class ResourceNotFoundError(MatchaException):
    code = 404


class WineSetEmptyError(MatchaException):
    code = 404


class ResourceAlreadyExist(MatchaException):
    code = 409


class ClientError(MatchaException):
    code = 400


class MethodNotAllowedError(MatchaException):
    code = 405


class LanguageError(MatchaException):
    code = 400

    def __init__(self, message=None, language=None):
        if message is None and language is not None:
            message = f'The language {language} is not supported'
        super().__init__(self, message)


class ValidationError(MatchaException):
    code = 400

    def __init__(self, message=""):
        super().__init__(self, message)


# usage not found
class TagError(MatchaException):
    code = 404

    def __init__(self, message="Tag was not found!"):
        super().__init__(self, message)


class GolemDoInvalidFunctionError(MatchaException):
    code = 400

    def __init__(self, message="Your message should start with 'golem do' plus at least a valid function"):
        super().__init__(self, message)


class EngineInstanceError(MatchaException):
    pass
