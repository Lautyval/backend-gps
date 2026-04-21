from fastapi import HTTPException

class UserException(HTTPException):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)

class UserNotFound(UserException):
    def __init__(self):
        super().__init__(detail="Usuario no encontrado", status_code=404)

class UserAlreadyExists(UserException):
    def __init__(self):
        super().__init__(detail="El usuario ya existe", status_code=409)
