## _BoilerPlate FastApi with Oauth2 (Google and Github) and JWT

### Running with docker

#### Pre-requisites:
- docker
- docker compose

#### Steps:
1. Create a file called `.env` with environment variables in the root of the project.
2. Build with `docker compose build`.
3. Run with `docker compose up`.
4. Create migrations if necessary `alembic revision --autogenerate -m "Initial"`
5In another terminal run the migrations `docker compose exec character alembic upgrade head`.
6Run test with `docker compose exec character pytest -vv`.

#### How to use:
- Go to `http://localhost:8000/docs`.
- You can also test the endpoints with your preferred rest client. (Postman/Insomnia).
- Inside the tests directory in the dummy folder is a Postman collection with the endpoints and payload.

#### Environment Variables (.env)
```
# SETTING
ENV=dev
SECRET_KEY=BoilerPlate2025

# POSTGRES
ENGINE=postgresql+psycopg2
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
POSTGRES_DB=character
POSTGRES_HOST=db
PGTZ=America/Argentina/Buenos_Aires

# AUTH GOOGLE
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
GOOGLE_AUTH_URL=https://accounts.google.com/o/oauth2/v2/auth
GOOGLE_TOKEN_URL=https://oauth2.googleapis.com/token
GOOGLE_JWKS_URL=https://www.googleapis.com/oauth2/v3/certs

# AUTH GITHUB
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/github/callback
GITHUB_AUTH_URL=https://github.com/login/oauth/authorize
GITHUB_TOKEN_URL=https://github.com/login/oauth/access_token
GITHUB_USER_INFO_URL=https://api.github.com/user

# JWT
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# FRONTEND
FRONTEND_URL=http://localhost:5173
```
