"""Parse chat text into character commands. The channel does not matter."""

from dataclasses import dataclass
from typing import Optional, Union

from core.schema.character_schema import PostCharacter, UpdateCharacter

HELP_TEXT = """\
Comandos de personajes:
• listar
• ver <id>
• crear Nombre | altura | masa | pelo | piel | ojos
• actualizar <id> masa=80
• eliminar <id>

También en varias líneas:
crear
nombre: Luke Skywalker
altura: 172
masa: 77
pelo: blond
piel: fair
ojos: blue

actualizar 12
masa: 80
ojos: green
"""

_VERBS = {
    "ayuda": "help",
    "help": "help",
    "hola": "help",
    "start": "help",
    "menu": "help",
    "listar": "list",
    "lista": "list",
    "list": "list",
    "ver": "get",
    "get": "get",
    "crear": "create",
    "create": "create",
    "actualizar": "update",
    "update": "update",
    "eliminar": "delete",
    "borrar": "delete",
    "delete": "delete",
}

_FIELDS = {
    "nombre": "name",
    "name": "name",
    "altura": "height",
    "height": "height",
    "masa": "mass",
    "mass": "mass",
    "pelo": "hair_color",
    "cabello": "hair_color",
    "hair": "hair_color",
    "hair_color": "hair_color",
    "piel": "skin_color",
    "skin": "skin_color",
    "skin_color": "skin_color",
    "ojos": "eye_color",
    "eye": "eye_color",
    "eye_color": "eye_color",
}

_NUMERIC = {"height", "mass"}
_CREATE_ORDER = ("name", "height", "mass", "hair_color", "skin_color", "eye_color")


class CommandError(Exception):
    """User-facing command syntax error."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass
class ParsedCommand:
    """A command ready to run against CharacterService."""

    kind: str
    character_id: Optional[int] = None
    payload: Optional[Union[PostCharacter, UpdateCharacter]] = None


def parse_command(text: str) -> ParsedCommand:
    """Parse a chat message into a character command."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if not lines:
        raise CommandError("Escribí ayuda para ver los comandos.")

    head, _, rest = lines[0].partition(" ")
    verb = _VERBS.get(head.lstrip("/").lower())
    rest = rest.strip()
    extra = lines[1:]

    if verb is None:
        raise CommandError("No entendí el comando. Escribí ayuda.")
    if verb == "help":
        return ParsedCommand(kind="help")
    if verb == "list":
        return ParsedCommand(kind="list")
    if verb == "get":
        return ParsedCommand(kind="get", character_id=_require_id(rest))
    if verb == "delete":
        character_id = _require_id(rest.split()[0] if rest else "")
        return ParsedCommand(kind="delete", character_id=character_id)
    if verb == "create":
        return ParsedCommand(kind="create", payload=_parse_create(rest, extra))
    return ParsedCommand(kind="update", **_parse_update(rest, extra))


def _parse_create(rest: str, extra: list[str]) -> PostCharacter:
    if "|" in rest and not extra:
        parts = [part.strip() for part in rest.split("|")]
        if len(parts) != 6:
            raise CommandError(
                "Para crear en una línea: "
                "crear Nombre | altura | masa | pelo | piel | ojos"
            )
        values = dict(zip(_CREATE_ORDER, parts))
        return PostCharacter(**_coerce_fields(values))

    fields: dict = {}
    if rest and ":" not in rest and "=" not in rest:
        fields["name"] = rest
    elif rest:
        fields.update(_parse_assignments([rest]))
    fields.update(_parse_assignments(extra))
    missing = [name for name in _CREATE_ORDER if name not in fields]
    if missing:
        raise CommandError(
            "Faltan datos para crear. Escribí ayuda para ver el formato.\n"
            "Faltan: " + ", ".join(missing)
        )
    return PostCharacter(**_coerce_fields({key: fields[key] for key in _CREATE_ORDER}))


def _parse_update(rest: str, extra: list[str]) -> dict:
    tokens = rest.split(maxsplit=1)
    if not tokens:
        raise CommandError("Indicá el id. Ejemplo: actualizar 12 masa=80")
    character_id = _require_id(tokens[0])
    assignments = []
    if len(tokens) > 1:
        assignments.append(tokens[1])
    assignments.extend(extra)
    fields = _parse_assignments(assignments)
    if not fields:
        raise CommandError("Indicá qué cambiar. Ejemplo: actualizar 12 masa=80")
    return {"character_id": character_id, "payload": UpdateCharacter(**_coerce_fields(fields))}


def _parse_assignments(lines: list[str]) -> dict:
    fields = {}
    for line in lines:
        pieces = line.split() if "=" in line and ":" not in line else [line]
        for piece in pieces:
            if ":" in piece:
                raw_key, raw_value = piece.split(":", 1)
            elif "=" in piece:
                raw_key, raw_value = piece.split("=", 1)
            else:
                raise CommandError(
                    f"No entendí '{piece}'. Usá campo: valor o campo=valor."
                )
            field = _FIELDS.get(raw_key.strip().lower())
            if field is None:
                raise CommandError(f"Campo desconocido: {raw_key.strip()}")
            value = raw_value.strip()
            if not value:
                raise CommandError(f"Falta el valor de {raw_key.strip()}.")
            fields[field] = value
    return fields


def _coerce_fields(fields: dict) -> dict:
    coerced = {}
    for key, value in fields.items():
        if key in _NUMERIC:
            try:
                coerced[key] = float(value)
            except (TypeError, ValueError) as exc:
                raise CommandError(f"{key} tiene que ser un número.") from exc
        else:
            coerced[key] = str(value).strip()
            if not coerced[key]:
                raise CommandError(f"Falta el valor de {key}.")
    return coerced


def _require_id(raw: str) -> int:
    token = raw.strip().split()[0] if raw.strip() else ""
    if not token:
        raise CommandError("Indicá el id del personaje.")
    try:
        return int(token)
    except ValueError as exc:
        raise CommandError("El id tiene que ser un número.") from exc
