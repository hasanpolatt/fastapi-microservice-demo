import logging
import os

import fastapi as _fastapi
import jwt
import pika
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import DecodeError
from pydantic import BaseModel

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

load_dotenv()
logging.basicConfig(level=logging.INFO)

JWT_SECRET = os.environ.get("JWT_SECRET")
AUTH_BASE_URL = os.environ.get("AUTH_BASE_URL")
RABBITMQ_URL = os.environ.get("RABBITMQ_URL")

connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_URL))
channel = connection.channel()
channel.queue_declare(queue="gatewayservice")
channel.queue_declare(queue="ocr_service")


async def jwt_validation(token: str = _fastapi.Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except DecodeError:
        raise HTTPException(status_code=401, detail="Invalid JWT token")


class GenerateUserToken(BaseModel):
    username: str
    password: str


class UserCredentials(BaseModel):
    username: str
    password: str


class UserRegistration(BaseModel):
    username: str
    email: str
    password: str


class GenerateOtp(BaseModel):
    email: str


class VerifyOtp(BaseModel):
    email: str
    otp: int


# Authentication routes


@app.post("/auth/login", tags=["Authentication Service"])
async def login(user_data: UserCredentials):
    try:
        response = requests.post(
            f"{AUTH_BASE_URL}/api/token",
            json={"username": user_data.username, "password": user_data.password},
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code, detail=response.json()
            )
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503, detail="Authentication service is unavailable"
        )


@app.post("/auth/register", tags=["Authentication Service"])
async def registeration(user_data: UserRegistration):
    try:
        response = requests.post(
            f"{AUTH_BASE_URL}/api/users",
            json={
                "name": user_data.name,
                "email": user_data.email,
                "password": user_data.password,
            },
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code, detail=response.json()
            )
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503, detail="Authentication service is unavailable"
        )


@app.post("/auth/generate_otp", tags=["Authentication Service"])
async def generate_otp(user_data: GenerateOtp):
    try:
        response = requests.post(
            f"{AUTH_BASE_URL}/api/users/generate_otp", json={"email": user_data.email}
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code, detail=response.json()
            )
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503, detail="Authentication service is unavailable"
        )
