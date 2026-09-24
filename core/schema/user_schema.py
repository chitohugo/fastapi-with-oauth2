from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from core.schema.base_schema import ModelBaseInfo


class BaseUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str = Field(..., examples=["user@example.com"])
    username: str = Field(..., examples=["jedi_master"])
    first_name: str = Field(..., examples=["Luke"])
    last_name: str = Field(..., examples=["Skywalker"])


class User(ModelBaseInfo, BaseUser):
    pass


class UpdateUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
