import hashlib
import hmac
import json

import pytest
from dependency_injector import providers

from config import settings
from core.messaging.service import MessagingService, clear_seen_messages
from core.services.whatsapp_provider import WhatsAppProvider
from main import AppCreator


class RecordingClient:
    def __init__(self):
        self.sent = []

    async def send_text(self, to: str, body: str) -> None:
        self.sent.append({"to": to, "body": body, "kind": "text"})


@pytest.fixture
def whatsapp_out(client):
    clear_seen_messages()
    recorder = RecordingClient()
    container = AppCreator._instance.container
    container.whatsapp_client.override(providers.Object(recorder))
    yield recorder
    container.whatsapp_client.reset_override()
    clear_seen_messages()


def _sign(body: bytes) -> str:
    digest = hmac.new(settings.whatsapp_app_secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _post_webhook(client, payload: dict, signature: str | None = None):
    raw = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if signature is not None:
        headers["X-Hub-Signature-256"] = signature
    else:
        headers["X-Hub-Signature-256"] = _sign(raw)
    return client.post("/api/v1/webhooks/whatsapp", content=raw, headers=headers)


def _text_payload(phone: str, text: str, message_id: str) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": phone,
                                    "id": message_id,
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ]
                        }
                    }
                ]
            }
        ],
    }


def test_help_is_plain_text(req, whatsapp_out):
    linked = req.put("/api/v1/whatsapp/me", json={"phone": "5491155550103"})
    assert linked.status_code == 200
    response = _post_webhook(req, _text_payload("5491155550103", "hola", "wamid.menu"))
    assert response.status_code == 200
    sent = whatsapp_out.sent[-1]
    assert sent["kind"] == "text"
    assert "listar" in sent["body"]


def test_verify_webhook(client):
    ok = client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.whatsapp_verify_token,
            "hub.challenge": "987654",
        },
    )
    assert ok.status_code == 200
    assert ok.text == "987654"

    rejected = client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong",
            "hub.challenge": "987654",
        },
    )
    assert rejected.status_code == 403


def test_webhook_rejects_bad_signature(client, whatsapp_out):
    payload = _text_payload("5491155550101", "listar", "wamid.reject")
    raw = json.dumps(payload).encode()
    response = client.post(
        "/api/v1/webhooks/whatsapp",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=deadbeef",
        },
    )
    assert response.status_code == 403
    assert whatsapp_out.sent == []


def test_unlinked_phone_gets_instructions(client, whatsapp_out):
    response = _post_webhook(
        client,
        _text_payload("5491155550101", "listar", "wamid.unlinked"),
    )
    assert response.status_code == 200
    assert "no está vinculado" in whatsapp_out.sent[0]["body"]
    assert "5491155550101" in whatsapp_out.sent[0]["body"]


def test_character_chat_flow(req, whatsapp_out):
    link = req.put("/api/v1/whatsapp/me", json={"phone": "+54 9 11 5555-0101"})
    assert link.status_code == 200
    assert link.json()["phone"] == "5491155550101"

    replaced = req.put("/api/v1/whatsapp/me", json={"phone": "5491155550102"})
    assert replaced.status_code == 200
    assert req.get("/api/v1/whatsapp/me").json()["phone"] == "5491155550102"

    created = _post_webhook(
        req,
        _text_payload(
            "5491155550102",
            "crear Luke Skywalker | 172 | 77 | blond | fair | blue",
            "wamid.create",
        ),
    )
    assert created.status_code == 200
    assert "Personaje creado" in whatsapp_out.sent[-1]["body"]
    assert whatsapp_out.sent[-1]["kind"] == "text"
    assert "*Luke Skywalker*" in whatsapp_out.sent[-1]["body"]

    listed = req.get("/api/v1/characters")
    assert listed.status_code == 200
    character = listed.json()[0]
    assert character["name"] == "Luke Skywalker"

    detailed = _post_webhook(
        req,
        _text_payload("5491155550102", f"ver {character['id']}", "wamid.get"),
    )
    assert detailed.status_code == 200
    assert "*Luke Skywalker*" in whatsapp_out.sent[-1]["body"]
    assert whatsapp_out.sent[-1]["kind"] == "text"

    listed_chat = _post_webhook(
        req,
        _text_payload("5491155550102", "listar", "wamid.list"),
    )
    assert listed_chat.status_code == 200
    assert whatsapp_out.sent[-1]["kind"] == "text"
    assert "*Luke Skywalker*" in whatsapp_out.sent[-1]["body"]
    assert f"#{character['id']}" in whatsapp_out.sent[-1]["body"]

    updated = _post_webhook(
        req,
        _text_payload("5491155550102", f"actualizar {character['id']} masa=80", "wamid.patch"),
    )
    assert updated.status_code == 200
    assert req.get(f"/api/v1/characters/{character['id']}").json()["mass"] == 80.0

    removed = _post_webhook(
        req,
        _text_payload("5491155550102", f"eliminar {character['id']}", "wamid.delete"),
    )
    assert removed.status_code == 200
    assert req.get("/api/v1/characters").json() == []

    req.delete("/api/v1/whatsapp/me")
    missing = req.get("/api/v1/whatsapp/me")
    assert missing.status_code == 404


def test_duplicate_message_id_does_not_run_twice(req, whatsapp_out):
    req.put("/api/v1/whatsapp/me", json={"phone": "5491155550199"})
    payload = _text_payload(
        "5491155550199",
        "crear Han Solo | 180 | 80 | brown | light | brown",
        "wamid.same",
    )
    assert _post_webhook(req, payload).status_code == 200
    assert _post_webhook(req, payload).status_code == 200
    assert len(whatsapp_out.sent) == 1
    assert len(req.get("/api/v1/characters").json()) == 1


def test_other_user_cannot_read_character_via_whatsapp(client, auth_token, whatsapp_out):
    owner_headers = {"Authorization": f"Bearer {auth_token}"}
    create_response = client.post(
        "/api/v1/characters",
        json={
            "name": "Leia Organa",
            "height": 150.0,
            "mass": 49.0,
            "hair_color": "brown",
            "skin_color": "light",
            "eye_color": "brown",
        },
        headers=owner_headers,
    )
    character_id = create_response.json()["id"]

    other = {
        "email": "other.whatsapp@example.com",
        "username": "otherwhatsapp",
        "first_name": "Other",
        "last_name": "User",
        "password": "secret123",
    }
    client.post("/api/v1/auth/signup", json=other)
    other_token = client.post(
        "/api/v1/auth/signin",
        json={"email": other["email"], "password": other["password"]},
    ).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}
    linked = client.put(
        "/api/v1/whatsapp/me",
        json={"phone": "5491155550188"},
        headers=other_headers,
    )
    assert linked.status_code == 200

    response = _post_webhook(
        client,
        _text_payload("5491155550188", f"ver {character_id}", "wamid.forbidden"),
    )
    assert response.status_code == 200
    assert "no es tuyo" in whatsapp_out.sent[-1]["body"]


def test_status_callback_and_non_text(client, whatsapp_out):
    status = _post_webhook(
        client,
        {"entry": [{"changes": [{"value": {"statuses": [{"id": "1", "status": "sent"}]}}]}]},
    )
    assert status.status_code == 200
    assert whatsapp_out.sent == []

    image = _post_webhook(
        client,
        {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "5491155550101",
                                        "id": "wamid.image",
                                        "type": "image",
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        },
    )
    assert image.status_code == 200
    assert "mensajes de texto" in whatsapp_out.sent[-1]["body"]


async def test_default_user_when_phone_is_not_linked():
    from unittest.mock import AsyncMock

    characters = AsyncMock()
    characters.get_list_for_user.return_value = []
    contacts = AsyncMock()
    contacts.find_by_external_id.return_value = None
    sender = AsyncMock()
    service = MessagingService(characters, contacts)
    clear_seen_messages()
    await service.handle(
        WhatsAppProvider(sender),
        _text_payload("5491100001111", "listar", "wamid.default"),
        default_user_id=4,
    )
    characters.get_list_for_user.assert_awaited_once_with(4)
    sender.send_text.assert_awaited()
    clear_seen_messages()
