from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.schemas.common import ErrorBody, ErrorResponse, ValidationIssue
from app.services.errors import ServiceError

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.exception_handler(ServiceError)
async def handle_service_error(
    request: Request, exc: ServiceError
) -> JSONResponse:
    response = ErrorResponse(
        error=ErrorBody(code=exc.code, message=str(exc))
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json", exclude_none=True),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    response = ErrorResponse(
        error=ErrorBody(
            code="validation_error",
            message="Request validation failed.",
            details=[
                ValidationIssue(
                    location=list(error["loc"]),
                    message=error["msg"],
                    type=error["type"],
                )
                for error in exc.errors()
            ],
        )
    )
    return JSONResponse(
        status_code=422,
        content=response.model_dump(mode="json", exclude_none=True),
    )
