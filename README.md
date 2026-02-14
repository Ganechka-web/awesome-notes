<p align="center">
    <img src="images/awesome-notes-logo.png">
</p>


# Awesome-notes

This is a API for writting notes in MarkDown format, it allows create users and notes, provides API Geteway authentification system

The general development purposes:
-  Learning FastAPI framework
-  Learning auth systems in microservices 
-  Learning CI/CD
-  Writting code in better architecture style as close as possible to real prodaction development 
-  Researching microservices architecture style and communications among micriservices
-  Improving testing style and quality

And it was just interesting as well)

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
- **RabbitMQ**: main communicatintg point among microservices


## Instalation :fire:

1. Copy this repo and cd to it

```bash
git copy <repo_url>
cd awesome-notes/
```

2. Next you need to create and fill config/development.env files, follow config/development.env.example which store in `/config`, or you can excecute following command to use test variables

```bash
cp config/development.env.example config/development.env
```

3. Finally execute following command to start project

```bash
docker compose -f docker-compose.dev.yml --env-file config/development.env up --build
```

4. Open your browser and follow one of these urls:
- `https://awesome-notes.com/auth/docs`: for auth service api docs
- `https://awesome-notes.com/user/docs`: for user service api docs
- `https://awesome-notes.com/notes/docs`: for notes service api docs

