from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from dotenv import load_dotenv
import os

# Calculate path to root .env file
# current file is in backend/app/main.py -> go up 3 levels to root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = FastAPI(title="LLM Data Engineer Exam Simulator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Data Engineer Exam Simulator API (JSON Mode)"}
