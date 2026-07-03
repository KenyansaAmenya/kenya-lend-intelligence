# Custom Exception Classes.
from fastapi import HTTPException, status

class BaseAppException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class AuthenticationError(BaseAppException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="AUTH_ERROR")

class AuthorizationError(BaseException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, code="FORBIDDEN")

class ResourceNotFoundError(BaseAppException):
    def __init__(self, message: str = "Resource"):
        super().__init__(f"{resource} not found", code="NOT FOUND")

class ValidationError(BaseAppException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, code="VALIDATION_ERROR")

class BusinessRuleError(BaseAppException):
    def __init__(self, message: str = "Business role violation"):
        super().__init__(message, code="BUSINESS_RULE_VIOLATION") 

class MLModelError(BaseAppException):
    def __init__(self, message: str = "Model inference failed"):
        super().__init__(message, code="ML_MODEL_ERROR")     

class ExternalServiceError(BaseAppException):
    def __init__(self, message: str = "External service"):
        super().__init__(f"{service} unavailable", code="EXTERNAL_SERVICE_ERROR")

class RateLimitError(BaseAppException):
    def __init__(self, message: str = "Rate limitexceeded"):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED")

# Exception to HTTP Response Mapping

def handle_app_exception(exc: BaseAppException):
    status_map = {
        "AUTH_ERROR": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "BUSINESS_RULE_VIOLATION": status.HTTP_100_CONTINUE,
        "ML_MODEL_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "RATE_LIMIT_EXCEEDED": status.HTTP_429_TOO_MANY_REQUESTS,
    }                                                         

    http_status = status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    return HTTPException(
        status_code=http_status,
        detail={
            "error": exc.code,
            "message": exc.message,
        }
    )

# TODO: Add error metrics collection (Prometheus counters per error code)
# TODO: Add error notification integration (PagerDuty, Slack)
# TODO: Add error sampling for Sentry integration

# Future Enhancements:
    # - Add error codes for client-side error handling
    # - Add i18n support for error messages
    # - Add error metrics collection    