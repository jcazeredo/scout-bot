class ScoutException(Exception):
    """Base exception for all scout-related errors"""
    pass

class ScoutConfigurationError(ScoutException):
    """Raised when there are problems with configuration"""
    pass

class ScoutExecutionError(ScoutException):
    """Raised when there are problems during execution"""
    pass