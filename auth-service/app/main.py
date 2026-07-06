from fastapi import FastAPI
from app.database import engine
from app import models
from app.routes import router
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="DocArmor Authentication Service",
    version="1.0.0",
    description ="Authentication microservice for DocArmor"
)

origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {"message": "Welcome to DocArmor Authentication Service!"}

@app.get("/health")
def health():
    return {"status": "running"}