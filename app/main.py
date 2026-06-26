from fastapi import FastAPI
from app.database import engine, Base
from app.models import users
from .routers import auth, user, admin

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get('/')
async def read_root():
    return {'message': 'A Api está funcionando'}

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(admin.router)