<p align="center">
    <img src="images/awesome-notes-logo.png">
</p>

<div align="center">

[![CI/CD](https://github.com/Ganechka-web/awesome-notes/actions/workflows/awesome_development.yml/badge.svg)](https://github.com/Ganechka-web/awesome-notes/actions) ![coverage](https://img.shields.io/badge/auth_service%20coverage-96%25-green) ![coverage](https://img.shields.io/badge/user_service%20coverage-95%25-green) ![coverage](https://img.shields.io/badge/notes_service%20coverage-98%25-green)

</div>

# Awesome-notes

A REST API for writing notes in Markdown format with user management and JWT-based authentication via API Gateway

## Key features :sparkles: 

- Fully async, isolated microservices based on FastAPI framework with dedicated PostgreSQL databases
- JWT authentication via API Gateway (Nginx) with Redis token storage
- Async microservices communication via RabbitMQ
- API Gateway routing via Nginx
- Unit and integration tests with more than 90% coverage
- CI/CD via GitHub Actions
- Onion-like structure in each microservice
- Fully automated and optimized project startup via docker-compose
- Secure Nginx via headers, CSP and rate limiting
 

## Tech stack  :wrench:
- languages and frameworks:

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/) ![SQLAlchemy](https://img.shields.io/badge/sqlalchemy-%23D71F00.svg?style=for-the-badge&logo=sqlalchemy&logoColor=white) [![PyPI](https://img.shields.io/pypi/v/dependency-injector?style=for-the-badge&label=Dependency%20Injector&color=blue)](https://pypi.org/project/dependency-injector/)
- Data storages:

![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) ![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white) 
- infrastructure:

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/) ![RabbitMQ](https://img.shields.io/badge/Rabbitmq-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white) ![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)
- Testing:

![Pytest](https://img.shields.io/badge/pytest-%23ffffff.svg?style=for-the-badge&logo=pytest&logoColor=2f9fe3) [![Testcontainers Python](https://img.shields.io/badge/Testcontainers_Python-5562FF?style=for-the-badge&logo=python&logoColor=white)](https://testcontainers.com/)


## Project architecture :triangular_ruler:

![Awesome-notes architecture structure](images/awesome-notes-architecture.png)

Project is based on isolated microservices which have got their own database and communicate by message broker:
- **NGINX**: reverse proxy and API Gateway
- **User service**: service for users management
- **Notes service**: service for user`s notes management
- **Auth service**: service for authentication and also user`s and credentials creating
- **DBs**: each service have got their own database 
- **Redis**: using for refresh token store
- **RabbitMQ**: main communication point among microservices


## Running tests :test_tube:

To run services' tests you should run the scripts/testing.sh which will use docker-compose.test.yml, special compose project for testing proposes 

- :penguin: Linux 

```bash
# awesome-notes/
chmod +x ./scripts/testing.sh
./scripts/testing.sh
```

- :window: Windows
 
Follow this **[guide](https://www.thewindowsclub.com/how-to-run-sh-or-shell-script-file-in-windows-10)** for executing bash scripts on Windows and then execute following command in your shell

```bash
bash scripts/testing.sh
```

## Quick start :fire:

1. Copy this repo and cd to it

```bash
git clone <repo_url>
cd awesome-notes/
```

2. Next you need to create and fill config/development.env files, follow config/development.env.example stored in the `/config` directory, or you can execute following command to use test variables

```bash
cp config/development.env.example config/development.env
```

3. Finally execute following command to start project

```bash
docker compose -f docker-compose.dev.yml --env-file config/development.env up --build
```

4. Open your browser and follow one of these urls:
- `http://localhost:8000/auth/docs`: for auth service api docs
- `http://localhost:8000/user/docs`: for user service api docs
- `http://localhost:8000/note/docs`: for notes service api docs

5. Or if you want to use canonical project version add this to your hosts file:
  
- :penguin: On Linux edit `/etc/hosts` **as root**

```
127.0.0.1	awesome-notes.com
```

- :window: On Windows edit `C:\Windows\System32\drivers\etc\hosts` **as Administrator**

```
127.0.0.1   awesome-notes.com
```

And instead of using http://localhost:8000 you are able to use https://awesome-notes.com/

## API Workflow Example :microscope:

- User creation:
  - Output: Created user UUID
  - Action: auth_service requests user_service to create user according user_data, gets created_user_id from user_service and then saves login and password with the same uuid

```bash
curl -X POST http://localhost:800/auth/register/ \
    -H "Content-Type: application/json" \
    -d '{"login":"awesome_login","password":"1234","user_data":{"username":"Maksim","gender":"male","age":"21"}}'
```

- User log-in:
  - Output: JWT token
  - Action: auth_service generates access and refresh tokens, returns access, sets access_token cookie and saves refresh token in Redis with ttl

```bash
curl -X POST http://localhost:8000/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"login":"awesome_login","password":"1234"}'
```

- Getting the Created user
  - Output: User json schema

```bash
curl -X GET http://localhost:8000/user/by-id/<your_created_user_uuid> \
    -b "access_token=<your_jwt_token>"
```

- User's note creation:
  - Output: Created note UUID

```bash
curl -X POST http://localhost:8000/note/create/ \
    -b "access_token=<your_jwt_token>" \
    -H "Content-Type: application/json" \
    -d '{"title":"My daily routine","content":"- Running\n- Training\n- Eating","owner_id":"<your_created_user_uuid>"}'
```

- All user's notes
  - Output: List of user's notes

```bash
curl -X GET http://localhost:8000/note/by-owner-id/<your_created_user_uuid> \
    -b "access_token=<your_jwt_token>"
```

- User deletion
  - Output: nothing with 204 status code
  - Action: user_service requests note_service to delete all user's notes by uuid and then deletes user
  
```bash
curl -X DELETE http://localhost:8000/user/delete/<your_created_user_uuid> \
    -b "access_token=<your_jwt_token>"
```