from pydantic import BaseModel


class AuthCredentialsRegisterSchema(BaseModel):
    login: str
    password: str

    class Config:
        from_attributes = True


class AuthCredentialsLoginSchema(AuthCredentialsRegisterSchema):
    pass


class AuthCredentialsSchema(AuthCredentialsRegisterSchema):
    id: int
