# Changelog

## Unreleased

### Added
- MCP server (stdio + optional Streamable HTTP profile) with character CRUD tools
- Health endpoints `/health` and `/ready`
- GitHub Actions CI (Docker + pytest)
- Makefile, `.env.example`, Docker improvements (healthchecks, dev/prod targets)
- Rate limiting on auth signup/signin (`slowapi`)
- User route `GET /users/me`; self-only access for user by id
- Partial PATCH for users and characters
- `user_id` on character API responses

### Changed
- Repositories and services migrated to async SQLAlchemy
- Global exception handlers for domain errors
- JWT unified on PyJWT (removed python-jose)
- Pydantic v2 `ConfigDict` on schemas; OpenAPI examples on main models
- Settings via pydantic-settings with validation (`SECRET_KEY` required)
- CORS configurable via `BACKEND_CORS_ORIGINS` (comma-separated)

### Fixed
- Duplicate email on signup returns 409
- MCP/Cursor path and Docker-based launch scripts
- Dependency conflicts (uvicorn vs mcp)
