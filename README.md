## _BoilerPlate FastApi with Clear Architecture_

#### _In the structure of the project there are three main layers following the Hexagonal Architecture or Clean Architecture approach:_
##### _User interface (UI) layer or external environment adapters:_
    Location: app
    Responsibility: Contains the UI, such as FastAPI routers, HTTP request and response handling in main.py, and other 
    UI-related elements.

##### _Business logic layer or use cases:_
    Location: core
    Responsibility: Contains business logic, including entities, services, and other components that implement 
    the application's business rules.

##### _Infrastructure or internal environment layer adapters:_
    Location: db
    Responsibility: Contains the implementation of the infrastructure, such as the mock database. 
    This layer provides concrete implementations for data persistence, but the business logic does not directly 
    depend on the implementation details.

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
SECRET_KEY=BoilerPlate2024

# POSTGRES
ENGINE=postgresql+psycopg2
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
POSTGRES_DB=character
POSTGRES_HOST=db
PGTZ=America/Argentina/Buenos_Aires
```
