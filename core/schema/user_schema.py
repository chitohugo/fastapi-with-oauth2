from core.schema.base_schema import ModelBaseInfo
from pydantic import BaseModel


class BaseUser(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class User(BaseUser):
    ...


class UpdateUser(BaseUser):
    ...
