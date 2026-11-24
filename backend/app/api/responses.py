from app.schemas.common import ErrorResponse

COMMON_ERROR_RESPONSES = {
    404: {"model": ErrorResponse, "description": "Resource not found"},
    409: {"model": ErrorResponse, "description": "Request conflicts with current state"},
    422: {"model": ErrorResponse, "description": "Request validation failed"},
}
