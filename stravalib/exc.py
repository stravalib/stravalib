

class AuthError(RuntimeError):
    pass

class LoginFailed(AuthError):
    pass

class LoginRequired(AuthError):
    """
    Login is required to perform specified action.
    """
    
class UnboundEntity(RuntimeError):
    """
    Exception used to indicate that a model Entity is not bound to client instances.
    """
    

class Fault(RuntimeError):
    """
    Container for exceptions raised by the remote server.
    """
        

