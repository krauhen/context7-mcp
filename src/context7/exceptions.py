# src//context7/exceptions.py
from fastapi import HTTPException
from context7.logger import logger


class AppException(HTTPException):
    def __init__(self, status_code: int, message: str):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        logger.error(f"[{self.__class__.__name__}] {message}")


class DocumentationNotFoundException(AppException):
    def __init__(self, status_code: int = 404, message: str = "Documentation not found."):
        super().__init__(status_code=status_code, message=message)


class LibraryNotFoundException(AppException):
    def __init__(self, status_code: int = 404, message: str = "No matching libraries found."):
        super().__init__(status_code=status_code, message=message)





