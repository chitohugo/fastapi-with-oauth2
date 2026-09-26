import hashlib
import hmac

import pytest

from core.messaging.commands import CommandError, parse_command
from core.services.whatsapp_protocol import (
    command_from_choice,
    outbound_phone,
    parse_inbound_messages,
    signature_is_valid,
    verify_subscription,
)


def test_argentina_outbound_phone_drops_mobile_prefix():
    assert outbound_phone("5491126358173") == "541126358173"
    assert outbound_phone("541126358173") == "541126358173"
    assert outbound_phone("15551234567") == "15551234567"


def test_parse_pipe_create():
    command = parse_command("crear Luke Skywalker | 172 | 77 | blond | fair | blue")
    assert command.kind == "create"
    assert command.payload.name == "Luke Skywalker"
    assert command.payload.height == 172.0
    assert command.payload.eye_color == "blue"


def test_parse_multiline_create_and_update():
    created = parse_command(
        "crear\nnombre: Leia Organa\naltura: 150\nmasa: 49\npelo: brown\npiel: light\nojos: brown"
    )
    assert created.payload.name == "Leia Organa"
    assert created.payload.mass == 49.0

    updated = parse_command("actualizar 12\nmasa: 80\nojos: green")
    assert updated.kind == "update"
    assert updated.character_id == 12
    assert updated.payload.mass == 80.0
    assert updated.payload.eye_color == "green"
    assert updated.payload.name is None


def test_parse_inline_update_and_help_alias():
    updated = parse_command("/actualizar 3 masa=78 ojos=blue")
    assert updated.character_id == 3
    assert updated.payload.mass == 78.0
    assert parse_command("hola").kind == "help"
    assert parse_command("eliminar 9").character_id == 9


def test_parse_rejects_unknown_and_incomplete():
    with pytest.raises(CommandError):
        parse_command("teletransportar")
    with pytest.raises(CommandError):
        parse_command("ver")
    with pytest.raises(CommandError):
        parse_command("crear Solo el nombre")


def test_signature_and_subscription():
    body = b'{"ok":true}'
    secret = "test-app-secret"
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert signature_is_valid(body, f"sha256={digest}", secret, "test") is True
    assert signature_is_valid(body, "sha256=deadbeef", secret, "test") is False
    assert signature_is_valid(body, None, "", "dev") is True
    assert signature_is_valid(body, None, "", "prod") is False
    assert verify_subscription("subscribe", "token", "token") is True
    assert verify_subscription("subscribe", "nope", "token") is False
    assert verify_subscription("unsubscribe", "token", "token") is False


def test_choice_ids_become_commands():
    assert command_from_choice("listar") == "listar"
    assert command_from_choice("ver:12") == "ver 12"
    assert command_from_choice("eliminar:3") == "eliminar 3"
    assert command_from_choice("menu:crear") == "menu:crear"
    assert command_from_choice("ver:abc") is None


def test_parse_inbound_ignores_statuses_and_keeps_text():
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "statuses": [{"id": "s1", "status": "read"}],
                            "messages": [
                                {
                                    "from": "+54 9 11 5555-0101",
                                    "id": "wamid.1",
                                    "type": "text",
                                    "text": {"body": "listar"},
                                },
                                {"from": "5491100000000", "id": "wamid.2", "type": "image"},
                            ],
                        }
                    }
                ]
            }
        ]
    }
    messages = parse_inbound_messages(payload)
    assert [(item.external_id, item.text, item.message_type) for item in messages] == [
        ("5491155550101", "listar", "text"),
        ("5491100000000", None, "image"),
    ]
