from fastapi import FastAPI
from app.database import engine, Base
from app.models import users
from .routers import auth, user, admin, trainer, gym_member

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(admin.router)
app.include_router(trainer.router)
app.include_router(gym_member.router)