from typing import List

from container import Container
from core.dependencies import get_current_user
from core.models.user import User
from core.schema.base_schema import Blank
from core.schema.character_schema import Character, PostCharacter, UpdateCharacter
from core.security import JWTBearer
from core.services.character_service import CharacterService
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/characters",
    tags=["characters"],
    dependencies=[Depends(JWTBearer())],
)


@router.get("", response_model=List[Character], dependencies=[Depends(get_current_user)])
@inject
async def get_characters(
    current_user: User = Depends(get_current_user),
    service: CharacterService = Depends(Provide[Container.character_service]),
):
    return await service.get_list_for_user(current_user.id)


@router.get("/{id}", response_model=Character, dependencies=[Depends(get_current_user)])
@inject
async def get_character(
    id: int,
    current_user: User = Depends(get_current_user),
    service: CharacterService = Depends(Provide[Container.character_service]),
):
    return await service.get_for_user(id, current_user.id)


@router.post("", response_model=Character)
@inject
async def create_character(
    payload: PostCharacter,
    service: CharacterService = Depends(Provide[Container.character_service]),
    current_user: User = Depends(get_current_user),
):
    payload.user_id = current_user.id
    return await service.add(payload)


@router.patch("/{id}", response_model=Character, dependencies=[Depends(get_current_user)])
@inject
async def update_character(
    id: int,
    payload: UpdateCharacter,
    current_user: User = Depends(get_current_user),
    service: CharacterService = Depends(Provide[Container.character_service]),
):
    return await service.patch_for_user(id, current_user.id, payload)


@router.delete("/{id}", response_model=Blank, dependencies=[Depends(get_current_user)])
@inject
async def delete_character(
    id: int,
    current_user: User = Depends(get_current_user),
    service: CharacterService = Depends(Provide[Container.character_service]),
):
    await service.remove_for_user(id, current_user.id)
    return Blank()
