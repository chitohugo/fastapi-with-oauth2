from pydantic import BaseModel, ConfigDict, Field


class SignIn(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str = Field(..., examples=["user@example.com"])
    password: str = Field(..., examples=["secret-password"])


class SignUp(SignIn):
    first_name: str = Field(..., examples=["Luke"])
    last_name: str = Field(..., examples=["Skywalker"])
    username: str = Field(..., examples=["jedi_master"])


class Payload(BaseModel):
    id: int
    email: str
    first_name: str | None = None


class SignInResponse(BaseModel):
    access_token: str
