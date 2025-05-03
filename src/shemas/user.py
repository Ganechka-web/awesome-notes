from datetime import datetime

from pydantic import BaseModel, Field


class UserCreateShema(BaseModel):
    username: str = Field(max_length=50)
    gender: str
    age: int 

    class Config:
        from_attributes = True
    
class UserUpgrateShema(UserCreateShema):
    pass

class UserOutputShema(UserCreateShema):
    id: int

class UserShema(UserOutputShema):
    password: str
