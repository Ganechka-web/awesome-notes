from uuid import UUID

from pydantic import BaseModel, Field, field_validator, field_serializer


class UserEventSchema(BaseModel):
    username: str = Field(max_length=50)
    gender: str
    age: int = Field(ge=18, le=110)

    class Config:
        from_attributes = True
    
    @field_validator('gender')
    @classmethod
    def validate_user_gender(cls, gender: str) -> str:
        genders = ('male', 'female', 
                   'unknown')
        if gender not in genders:
            raise ValueError(f'Gender can be only {', '.join(genders)}')
        return gender
    

class UserEventCreateSchema(UserEventSchema):
    id: UUID

    @field_serializer('id')
    def serialize_id(self, id: UUID, _info) -> str:
        return str(id)


class AuthCredentialsRegisterSchema(BaseModel):
    login: str
    password: str
    user_data: UserEventSchema

    class Config:
        from_attributes = True


class AuthCredentialsLoginSchema(BaseModel):
    login: str
    password: str
    
    class Config:
        from_attributes = True


class AuthCredentialsSchema(AuthCredentialsLoginSchema):
    id: int
