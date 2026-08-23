class TenderIQException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationException(TenderIQException):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class AuthenticationException(TenderIQException):
    def __init__(self, message: str):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationException(TenderIQException):
    def __init__(self, message: str):
        super().__init__(message, "AUTHORIZATION_ERROR")


class ResourceNotFoundException(TenderIQException):
    def __init__(self, message: str):
        super().__init__(message, "NOT_FOUND")


class BusinessRuleViolationException(TenderIQException):
    def __init__(self, message: str):
        super().__init__(message, "BUSINESS_RULE_VIOLATION")


class AIProcessingException(TenderIQException):
    def __init__(self, message: str):
        super().__init__(message, "AI_PROCESSING_ERROR")


class StorageException(TenderIQException):
    def __init__(self, message: str):
        super().__init__(message, "STORAGE_ERROR")


class InternalServerException(TenderIQException):
    def __init__(self, message: str):
        super().__init__(message, "INTERNAL_SERVER_ERROR")