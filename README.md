<p align="center">
    <img src="images/awesome-notes-logo.png">
</p>

# <h1 align="center">Awesome-notes</h1>
This is a API for writting notes in MarkDown format, it allows create users and notes, provides API Geteway authentification system


The general development purposes:
-  Learning FastAPI framework
-  Learning auth systems in microservices 
-  Writting code in better architecture style as close as possible to real prodaction development 
-  Researching microservices architecture style and communications among micriservices
-  Improving testing style and quality

And it was just interesting as well)


## Project architecture

![Awesome-notes architecture structure](images/awesome-notes-architecture.png)

Project is based on isolated microservices which have got their own database and communicate by message broker:
- **NGINX**: reverse proxy and API Gateway
- **User service**: service for users management
- **Notes service**: service for user`s notes management
- **Auth service**: service for authentication and also user`s and credentials creating
- **DBs**: each service have got their own database 
- **Redis**: using for refresh token store
- **RabbitMQ**: main communicatintg point among microservices


## Instalation

1. Firstly you need to fill .env files, follow .env.example which store in `/config`, `auth_service/`, `user_service/` and `notes/service/` dirs.

2. Next step is cd to `awesome-notes/` and run following code for launching docker-compose project

```bash
docker compose --env-file config/development.env up --build
``` 

3. Open your browser and follow one of these urls:
- `https://awesome-notes/auth/docs`: for auth service api docs
- `https://awesome-notes/user/docs`: for user service api docs
- `https://awesome-notes/notes/docs`: for notes service api docs

