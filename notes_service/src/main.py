from fastapi import FastAPI

from api.endpoints.note import notes_router


app = FastAPI()

app.include_router(notes_router)
