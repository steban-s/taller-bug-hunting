from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.database import engine, Base
from core.config import settings

from models.orden import Orden  
from models.mecanico import  Mecanico  
from models.repuesto import Repuesto 

from routers import ordenes, mecanicos

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(ordenes.router)
app.include_router(mecanicos.router)