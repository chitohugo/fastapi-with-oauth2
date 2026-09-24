from container import Container
from core.dependencies import get_current_user, require_self
from core.models.user import User
from core.schema.base_schema import Blank
from core.schema.user_schema import UpdateUser, User as UserSchema
from core.security import JWTBearer
from core.services.user_service import UserService
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(JWTBearer())],
)


@router.get("/me", response_model=UserSchema)
@inject
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{id}", response_model=UserSchema)
@inject
async def get_user(
    id: int,
    _owner: User = Depends(require_self),
    service: UserService = Depends(Provide[Container.user_service]),
):
    return await service.get_by_id(id)


@router.patch("/{id}", response_model=UserSchema)
@inject
async def update_user(
    id: int,
    user: UpdateUser,
    _owner: User = Depends(require_self),
    service: UserService = Depends(Provide[Container.user_service]),
):
    return await service.patch(id, user)


@router.delete("/{id}", response_model=Blank)
@inject
async def delete_user(
    id: int,
    _owner: User = Depends(require_self),
    service: UserService = Depends(Provide[Container.user_service]),
):
    await service.remove_by_id(id)
    return Blank()
