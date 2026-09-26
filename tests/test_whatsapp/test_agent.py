import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import httpx
import pytest

from app.messaging.llm_agent import LlmCharacterAgent
from core.messaging.replies import OutboundReply
from core.messaging.service import MessagingService, clear_seen_messages
from core.services.whatsapp_provider import WhatsAppProvider
from tests.test_api.test_whatsapp import _text_payload


class _Row:
    id = 7
    name = "Leia"
    height = 150.0
    mass = 49.0
    hair_color = "brown"
    skin_color = "light"
    eye_color = "brown"
    user_id = 4
    created_at = datetime.now(timezone.utc)
    updated_at = created_at


def _completion(message: dict) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": message}]})


@pytest.mark.asyncio
async def test_phrase_lists_characters_through_the_mcp_tool():
    characters = AsyncMock()
    characters.get_list_for_user.return_value = []
    seen = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["n"] += 1
        body = json.loads(request.content)
        assert body["tools"][0]["function"]["name"] == "list_characters"
        if seen["n"] == 1:
            return _completion(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "list_characters", "arguments": "{}"},
                        }
                    ],
                }
            )
        assert any(item["role"] == "tool" for item in body["messages"])
        return _completion({"role": "assistant", "content": "No tenés personajes."})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        agent = LlmCharacterAgent(characters, client, "test-key", "test-model", "https://llm.test/v1")
        reply = await agent.respond(4, "5491100001111", "qué personajes tengo")

    assert reply.body == "No tenés personajes."
    characters.get_list_for_user.assert_awaited_once_with(4)


@pytest.mark.asyncio
async def test_phrase_creates_a_character_card():
    characters = AsyncMock()
    characters.add.return_value = _Row()

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if not any(item["role"] == "tool" for item in body["messages"]):
            return _completion(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_2",
                            "type": "function",
                            "function": {
                                "name": "create_character",
                                "arguments": json.dumps(
                                    {
                                        "name": "Leia",
                                        "height": 150,
                                        "mass": 49,
                                        "hair_color": "brown",
                                        "skin_color": "light",
                                        "eye_color": "brown",
                                    }
                                ),
                            },
                        }
                    ],
                }
            )
        return _completion({"role": "assistant", "content": "Listo, creé a Leia."})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        agent = LlmCharacterAgent(characters, client, "test-key", "test-model", "https://llm.test/v1")
        reply = await agent.respond(4, "5491100001111", "creá a Leia")

    assert reply.kind == "character"
    assert reply.headline == "Listo, creé a Leia."
    assert reply.character.name == "Leia"
    characters.add.assert_awaited()


@pytest.mark.asyncio
async def test_free_text_uses_the_agent_and_menu_taps_do_not():
    agent = AsyncMock()
    agent.respond.return_value = OutboundReply("Decime altura, masa y colores.")
    characters = AsyncMock()
    characters.get_list_for_user.return_value = []
    contacts = AsyncMock()
    contacts.find_by_external_id.return_value = None
    sender = AsyncMock()
    service = MessagingService(characters, contacts, agent=agent)
    clear_seen_messages()
    await service.handle(
        WhatsAppProvider(sender),
        _text_payload("5491100001111", "Creá un personaje", "wamid.phrase"),
        default_user_id=4,
    )
    agent.respond.assert_awaited_once_with(4, "5491100001111", "Creá un personaje")

    clear_seen_messages()
    await service.handle(
        WhatsAppProvider(sender),
        _text_payload("5491100001111", "listar", "wamid.menu"),
        default_user_id=4,
    )
    characters.get_list_for_user.assert_awaited_once_with(4)
    assert agent.respond.await_count == 1
    clear_seen_messages()
