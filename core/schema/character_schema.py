from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from core.schema.base_schema import ModelBaseInfo


class BaseCharacter(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., examples=["Luke Skywalker"])
    height: float = Field(..., examples=[172.0])
    mass: float = Field(..., examples=[77.0])
    hair_color: str = Field(..., examples=["blond"])
    skin_color: str = Field(..., examples=["fair"])
    eye_color: str = Field(..., examples=["blue"])


class Character(ModelBaseInfo, BaseCharacter):
    user_id: Optional[int] = None


class PostCharacter(BaseCharacter):
    user_id: Optional[int] = None


class UpdateCharacter(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    height: Optional[float] = None
    mass: Optional[float] = None
    hair_color: Optional[str] = None
    skin_color: Optional[str] = None
    eye_color: Optional[str] = None
