class Error(Exception):
   """Base class for other exceptions"""
   pass

class AuthError(Error):
   """Raised when the authentication fails"""
   pass

class ValueTooLargeError(Error):
   """Raised when the input value is too large"""
   pass

class NotLoggedInError(Error):
    """Raised when user is not loged in"""
    pass