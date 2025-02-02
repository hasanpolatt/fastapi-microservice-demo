import base64
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

from gateway import rpc_client
from models.gateway_schemas import (GenerateOtp, UserCredentials,
                                    UserRegistration)

app = FastAPI()
# Defining an OAuth2 scheme for token-based authentication.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Loading environment variables from the .env file.
load_dotenv()

# Setting up logging configuration to display logs at the INFO level.
logging.basicConfig(level=logging.INFO)

# Fetching environment variables for JWT secret, authentication service URL, and RabbitMQ connection URL.
JWT_SECRET = os.environ.get("JWT_SECRET")
AUTH_BASE_URL = os.environ.get("AUTH_BASE_URL")
RABBITMQ_URL = os.environ.get("RABBITMQ_URL")

# Establishing a connection to RabbitMQ.
# Declaring two RabbitMQ queues: one for the gateway service and one for the OCR service.
connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_URL))
channel = connection.channel()
channel.queue_declare(queue="gatewayservice")
channel.queue_declare(queue="ocr_service")


# A function to validate JWT tokens. If the token is invalid, an HTTP 401 error is raised.
async def jwt_validation(token: str = _fastapi.Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except DecodeError:
        raise HTTPException(status_code=401, detail="Invalid JWT token")


# Authentication routes
# Endpoint to handle user login. Sends credentials to the authentication service to get a token.
@app.post("/auth/login", tags=["Authentication Service"])
async def login(user_data: UserCredentials):
    try:
        response = requests.post(
            f"{AUTH_BASE_URL}/api/token",
            json={"username": user_data.username, "password": user_data.password},
        )
        if response.status_code == 200:
            return response.json()  # Returns the token if authentication is successful.
        else:
            raise HTTPException(
                status_code=response.status_code, detail=response.json()
            )  # Raises an HTTP exception if the service returns an error.
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503, detail="Authentication service is unavailable"
        )  # Raises an HTTP exception if the authentication service is unreachable.


# Endpoint to handle user registration. Sends user data to the authentication service.
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


# Endpoint to generate an OTP (One-Time Password) for the given email address.
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


@app.post("/ocr", tags=["Machine learning Service"])
def ocr(file: UploadFile = File(...), payload: dict = _fastapi.Depends(jwt_validation)):
    """
    Handles OCR requests by accepting an uploaded file and user details,
    then forwarding them to the OCR microservice via RabbitMQ.
    """

    # Save the uploaded file temporarily on the server
    with open(file.filename, "wb") as buffer:
        buffer.write(file.file.read())

    # Create an instance of the OCR RPC client
    ocr_rpc = rpc_client.OcrRpcClient()

    # Read the saved file and encode its contents in Base64 format
    with open(file.filename, "rb") as buffer:
        file_data = buffer.read()
        file_base64 = base64.b64encode(file_data).decode()

    # Prepare the request payload to send to the OCR microservice
    request_json = {
        "user_name": payload["username"],
        "user_email": payload["email"],
        "user_id": payload["id"],
        "file": payload["file"],
    }

    # Send the request to the OCR microservice via RabbitMQ
    response = ocr_rpc.call(request_json)

    # Remove the temporary file after processing
    os.remove(file.filename)
    return response


# Entry point to run the FastAPI app using Uvicorn.
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=6000, reload=True)
