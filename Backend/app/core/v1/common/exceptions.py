from typing import Optional

NOT_FOUND_MESSAGE = "{} not found or user does not have access"
CONFLICT_MESSAGE = "{} already exists"


class NotFoundOrAccessException(Exception):
    """Exception raised for any <object> not found or user does not have access"""

    def __init__(self, object_type: Optional[str] = None, message=NOT_FOUND_MESSAGE):
        if object_type:
            self.message = message.format(object_type)
        else:
            self.message = message
        super().__init__(self.message)


class ConflictException(Exception):
    """Exception raised when trying to create a resource that already exists"""

    def __init__(self, object_type: Optional[str] = None, message=CONFLICT_MESSAGE):
        if object_type:
            self.message = message.format(object_type)
        else:
            self.message = message
        super().__init__(self.message)


# ===========================================================================================


class BaseException(Exception):
    """Base exception class for all exceptions"""

    def __init__(self, message: str, detail: Optional[str] = None):
        self.message = message
        self.detail = detail
        full_message = self.message
        if self.detail:
            full_message += ": " + self.detail
        super().__init__(full_message)


class InvalidDocumentException(BaseException):
    """Exception raised for any invalid document"""

    def __init__(self, detail: Optional[str] = None):
        self.message = "Invalid document"
        super().__init__(self.message, detail)


class ChunkingError(BaseException):
    """Exception raised for any error in chunking"""

    def __init__(self, detail: Optional[str] = None):
        self.message = "Error in chunking"
        super().__init__(self.message, detail)


class IngestionError(BaseException):
    """Exception raised for errors during document ingestion."""

    def __init__(self, detail: Optional[str] = None):
        self.message = "Error in ingestion"
        super().__init__(self.message, detail)


class LlmException(BaseException):
    """Exception raised for errors in LLM operations"""

    def __init__(self, detail: Optional[str] = None):
        self.message = "Error in LLM operation"
        super().__init__(self.message, detail)