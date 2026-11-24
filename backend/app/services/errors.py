class ServiceError(Exception):
    status_code = 400
    code = "service_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)


class NotFoundError(ServiceError):
    status_code = 404
    code = "not_found"


class ConflictError(ServiceError):
    status_code = 409
    code = "conflict"


class InvalidOperationError(ServiceError):
    status_code = 422
    code = "invalid_operation"


class AssistantConfigurationError(ServiceError):
    status_code = 503
    code = "assistant_not_configured"


class AssistantWorkflowError(ServiceError):
    status_code = 502
    code = "assistant_workflow_failed"
