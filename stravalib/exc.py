

class AuthError(RuntimeError):
    pass

class LoginFailed(AuthError):
    pass

class LoginRequired(AuthError):
    """
    Login is required to perform specified action.
    """

class Fault(RuntimeError):
    """
    Container for exceptions raised by the remote server.
    """

