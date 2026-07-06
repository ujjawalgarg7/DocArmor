from fastapi import FastAPI
from app.database import engine
from app import models
from app.routes import router

models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="DocArmor Authentication Service",
    version="1.0.0",
    description ="Authentication microservice for DocArmor"
)

app.include_router(router)

@app.get("/")
def root():
    return {"message": "Welcome to DocArmor Authentication Service!"}

@app.get("/health")
def health():
    return {"status": "running"}