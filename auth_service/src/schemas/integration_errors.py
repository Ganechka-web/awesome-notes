from pydantic import BaseModel


class BaseServiceIntegrationErrorSchema(BaseModel):
    """Base class for integration errors schemas"""
    service_name: str = "user_service"
    http_status_code: int
    message: str


class UserServiceCreationErrorSchema(BaseServiceIntegrationErrorSchema):
    """
    UserServiceCreationErrorSchema uses when user_service 
    returns an error because of conflict with a new user
    """
    http_status_code: int = 409
    