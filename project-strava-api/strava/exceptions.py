"""
Custom exceptions for Strava API interactions
"""


class StravaAPIException(Exception):
    """Base exception for Strava API errors"""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class StravaAuthException(StravaAPIException):
    """Exception raised for authentication/authorization errors"""
    pass


class StravaRateLimitException(StravaAPIException):
    """Exception raised when API rate limits are exceeded"""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class StravaTokenExpiredException(StravaAuthException):
    """Exception raised when access token is expired and cannot be refreshed"""
    pass


class StravaInvalidTokenException(StravaAuthException):
    """Exception raised when the provided token is invalid"""
    pass


class StravaNetworkException(StravaAPIException):
    """Exception raised for network-related errors"""
    pass


class StravaDataNotFoundException(StravaAPIException):
    """Exception raised when requested data is not found"""
    pass