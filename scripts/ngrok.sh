#!/bin/sh
# Expose the API container on a public HTTPS URL (WhatsApp webhook).
set -eu

if [ -z "${NGROK_AUTHTOKEN:-}" ]; then
  echo "NGROK_AUTHTOKEN is empty. Add it to .env and restart ngrok." >&2
  exit 1
fi

if [ -n "${NGROK_URL:-}" ]; then
  exec ngrok --config=/var/lib/ngrok/ngrok.yml http \
    --authtoken "$NGROK_AUTHTOKEN" \
    --log=stdout \
    --url "$NGROK_URL" \
    character:8000
fi

exec ngrok --config=/var/lib/ngrok/ngrok.yml http \
  --authtoken "$NGROK_AUTHTOKEN" \
  --log=stdout \
  character:8000
