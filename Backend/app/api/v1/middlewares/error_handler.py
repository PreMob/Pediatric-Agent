import traceback
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.v1.common.exceptions import (
    NotFoundOrAccessException,
    ConflictException,
    BaseException as CustomBaseException,
    InvalidDocumentException,
    ChunkingError,
    IngestionError,
    LlmException
)
from app.core.v1.common.logger import get_logger

logger = get_logger("error_handler")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException as e:
            # Let FastAPI's HTTPExceptions pass through unchanged
            logger.warning(f"HTTP Exception: {e.status_code} - {e.detail}")
            raise e
        except NotFoundOrAccessException as e:
            # Handle not found or access exceptions with 404 status
            logger.warning(f"Not found or access denied: {str(e)}")
            return JSONResponse(
                status_code=404, 
                content={"detail": str(e), "type": "not_found_or_access"}
            )
        except ConflictException as e:
            # Handle conflict exceptions with 409 status
            logger.warning(f"Conflict exception: {str(e)}")
            return JSONResponse(
                status_code=409, 
                content={"detail": str(e), "type": "conflict"}
            )
        except InvalidDocumentException as e:
            # Handle invalid document exceptions with 400 status
            logger.warning(f"Invalid document: {str(e)}")
            return JSONResponse(
                status_code=400, 
                content={"detail": str(e), "type": "invalid_document"}
            )
        except (ChunkingError, IngestionError) as e:
            # Handle document processing errors with 422 status
            logger.error(f"Document processing error: {str(e)}")
            return JSONResponse(
                status_code=422, 
                content={"detail": str(e), "type": "processing_error"}
            )
        except LlmException as e:
            # Handle LLM exceptions with 503 status (service unavailable)
            logger.error(f"LLM error: {str(e)}")
            return JSONResponse(
                status_code=503, 
                content={"detail": str(e), "type": "llm_error"}
            )
        except CustomBaseException as e:
            # Handle other custom base exceptions with 500 status
            logger.error(f"Custom exception: {str(e)}")
            return JSONResponse(
                status_code=500, 
                content={"detail": str(e), "type": "custom_error"}
            )
        except ValueError as e:
            # Handle validation errors with 400 status
            logger.warning(f"Validation error: {str(e)}")
            return JSONResponse(
                status_code=400, 
                content={"detail": str(e), "type": "validation_error"}
            )
        except PermissionError as e:
            # Handle permission errors with 403 status
            logger.warning(f"Permission error: {str(e)}")
            return JSONResponse(
                status_code=403, 
                content={"detail": str(e), "type": "permission_error"}
            )
        except Exception as e:
            # Handle any other exceptions as 500 internal server errors
            logger.error(f"Unhandled exception: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return JSONResponse(
                status_code=500, 
                content={
                    "detail": "An unexpected error occurred", 
                    "type": "internal_error"
                }
            )