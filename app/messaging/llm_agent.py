"""Turn a WhatsApp sentence into the character tools shared with MCP."""

import json
import logging
from typing import Optional

from httpx import AsyncClient
from mcp.server.fastmcp.exceptions import ToolError

from core.messaging.replies import CharacterSnapshot, OutboundReply
from core.schema.character_schema import UpdateCharacter
from core.services.character_service import CharacterService

logger = logging.getLogger("client-ai")

_HISTORY_LIMIT = 8
_SYSTEM = """\
Sos el asistente de una app de personajes, en un chat de WhatsApp.
El usuario habla en español, con frases normales. No espera comandos.
Usá las tools para listar, ver, crear, actualizar o eliminar.
Si faltan altura, masa, pelo, piel u ojos, preguntalos. No los inventes.
"Este", "ese" o "el último" se refiere al personaje marcado como [personaje #id] en el historial.
Si hay varios y no se entiende cuál, listá y preguntá.
Respondé en español, corto, de vos. No menciones tools ni comandos.
No leas en voz alta las marcas [personaje #id].
"""

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_characters",
            "description": "Lista los personajes del usuario.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_character",
            "description": "Trae un personaje por id.",
            "parameters": {
                "type": "object",
                "properties": {"character_id": {"type": "integer"}},
                "required": ["character_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_character",
            "description": "Crea un personaje. Todos los datos son obligatorios.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "height": {"type": "number"},
                    "mass": {"type": "number"},
                    "hair_color": {"type": "string"},
                    "skin_color": {"type": "string"},
                    "eye_color": {"type": "string"},
                },
                "required": [
                    "name",
                    "height",
                    "mass",
                    "hair_color",
                    "skin_color",
                    "eye_color",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_character",
            "description": "Cambia solo los campos que el usuario pidió.",
            "parameters": {
                "type": "object",
                "properties": {
                    "character_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "height": {"type": "number"},
                    "mass": {"type": "number"},
                    "hair_color": {"type": "string"},
                    "skin_color": {"type": "string"},
                    "eye_color": {"type": "string"},
                },
                "required": ["character_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_character",
            "description": "Elimina un personaje por id.",
            "parameters": {
                "type": "object",
                "properties": {"character_id": {"type": "integer"}},
                "required": ["character_id"],
                "additionalProperties": False,
            },
        },
    },
]


class LlmCharacterAgent:
    """Chat completion with the same character tools registered on the MCP server."""

    def __init__(
        self,
        character_service: CharacterService,
        http_client: AsyncClient,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
    ):
        self.characters = character_service
        self.http_client = http_client
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._history: dict[str, list[dict]] = {}

    async def respond(self, user_id: int, chat_id: str, text: str) -> OutboundReply:
        """Call the model until it answers or runs out of tool rounds."""
        messages = [
            {"role": "system", "content": _SYSTEM},
            *self._history.get(chat_id, []),
            {"role": "user", "content": text},
        ]
        outcome = None
        try:
            for _ in range(4):
                message = await self._complete(messages)
                tool_calls = message.get("tool_calls") or []
                if not tool_calls:
                    speech = _message_text(message) or "Listo."
                    self._remember(chat_id, text, speech, outcome)
                    return _present(speech, outcome)
                messages.append(message)
                for call in tool_calls:
                    payload, outcome = await self._run_tool(user_id, call, outcome)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.get("id") or "",
                            "content": payload,
                        }
                    )
        except Exception:
            logger.exception("Language model failed for user %s", user_id)
            return OutboundReply("No pude entender el pedido. Probá de nuevo en un momento.")
        return OutboundReply("No llegué a completar la acción. Decime de nuevo qué querés hacer.")

    async def _complete(self, messages: list[dict]) -> dict:
        response = await self.http_client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": messages, "tools": _TOOLS, "temperature": 0.2},
            timeout=25.0,
        )
        if response.is_error:
            logger.error(
                "Language model HTTP %s for model %s: %s",
                response.status_code,
                self.model,
                response.text,
            )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]

    async def _run_tool(
        self,
        user_id: int,
        call: dict,
        previous: Optional[dict],
    ) -> tuple[str, Optional[dict]]:
        """Execute one tool. A failed call keeps the previous successful outcome."""
        function = call.get("function") or {}
        name = str(function.get("name") or "")
        try:
            arguments = _arguments(function.get("arguments"))
            result, outcome = await self._dispatch(user_id, name, arguments)
            return json.dumps(result, ensure_ascii=False), outcome
        except ToolError as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False), previous
        except (TypeError, ValueError, KeyError) as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False), previous

    async def _dispatch(self, user_id: int, name: str, arguments: dict) -> tuple[object, dict]:
        from app.mcp.tools import (
            create_character,
            delete_character,
            get_character,
            list_characters,
            update_character,
        )

        if name == "list_characters":
            rows = await list_characters(self.characters, user_id)
            return rows, {"kind": "list", "rows": rows}
        if name == "get_character":
            row = await get_character(self.characters, user_id, int(arguments["character_id"]))
            return row, {"kind": "character", "row": row}
        if name == "create_character":
            row = await create_character(
                self.characters,
                user_id,
                str(arguments["name"]),
                float(arguments["height"]),
                float(arguments["mass"]),
                str(arguments["hair_color"]),
                str(arguments["skin_color"]),
                str(arguments["eye_color"]),
            )
            return row, {"kind": "character", "row": row}
        if name == "update_character":
            payload = UpdateCharacter(
                name=arguments.get("name"),
                height=_optional_float(arguments.get("height")),
                mass=_optional_float(arguments.get("mass")),
                hair_color=arguments.get("hair_color"),
                skin_color=arguments.get("skin_color"),
                eye_color=arguments.get("eye_color"),
            )
            row = await update_character(
                self.characters,
                user_id,
                int(arguments["character_id"]),
                payload,
            )
            return row, {"kind": "character", "row": row}
        if name == "delete_character":
            character_id = int(arguments["character_id"])
            result = await delete_character(self.characters, user_id, character_id)
            return result, {"kind": "deleted", "id": character_id}
        raise ValueError(f"Tool desconocida: {name}")

    def _remember(
        self,
        chat_id: str,
        user_text: str,
        speech: str,
        outcome: Optional[dict],
    ) -> None:
        note = speech
        if outcome and outcome.get("kind") == "character":
            row = outcome["row"]
            note = f"{speech}\n[personaje #{row['id']} {row['name']}]"
        bucket = self._history.setdefault(chat_id, [])
        bucket.append({"role": "user", "content": user_text})
        bucket.append({"role": "assistant", "content": note})
        del bucket[:-_HISTORY_LIMIT]


def _arguments(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Los argumentos de la tool no son un objeto.")
    return parsed


def _optional_float(value) -> Optional[float]:
    if value is None or value == "":
        return None
    return float(value)


def _message_text(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text") or ""))
        return "\n".join(part for part in parts if part).strip()
    return ""


def _present(speech: str, outcome: Optional[dict]) -> OutboundReply:
    if not outcome:
        return OutboundReply(speech)
    if outcome["kind"] == "list" and outcome["rows"]:
        return OutboundReply(
            speech,
            kind="list",
            characters=tuple(_snapshot(row) for row in outcome["rows"][:10]),
        )
    if outcome["kind"] == "character":
        return OutboundReply(
            "",
            kind="character",
            headline=speech,
            character=_snapshot(outcome["row"]),
        )
    return OutboundReply(speech)


def _snapshot(row: dict) -> CharacterSnapshot:
    return CharacterSnapshot(
        id=int(row["id"]),
        name=str(row["name"]),
        height=float(row["height"]),
        mass=float(row["mass"]),
        hair_color=str(row["hair_color"]),
        skin_color=str(row["skin_color"]),
        eye_color=str(row["eye_color"]),
    )
